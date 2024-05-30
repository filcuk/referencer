from nicegui import app, ui
from nicegui.events import KeyEventArguments
import csv
import inspect, os.path
import re
import webbrowser
import argparse
import strictyaml

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', type=bool)

args = parser.parse_args()

debug = False if args.debug is None else args.debug

filename = inspect.getframeinfo(inspect.currentframe()).filename
path     = os.path.dirname(os.path.abspath(filename))
dataFile = 'data_sample.csv' if debug else 'data.csv'

# %% Definitions
def openDataFile():
    customNotify('Opening file...')
    webbrowser.open(f'{path}\\{dataFile}')

def writeToClipboard(text):
    if trim.value:
        # Replace any 0's in the middle of a string; https://regex101.com/r/5a5jxD/1
        output = re.sub(r'^(\D*)0*(\d+.*)', r'\1\2', text)
    else:
        output = text
    
    if len(output) == 0 or output == 'NA':
        customNotify('Nothing to copy', group='copy')
    else:
        ui.clipboard.write(output)
        customNotify(f'Copied: {output}', group='copy')

def handleKey(e: KeyEventArguments):
    if e.key == 'Escape' and e.action.keydown:
        if debug:
            customNotify('Cannot shutdown in debug mode')
        else:
            app.shutdown()
    elif e.modifiers.ctrl and e.action.keydown and focus['filter'] == False:
        match e.key:
            case 'f': filter.run_method('focus')
            case 't': trim.value = not trim.value
            case 'a': archived.value = not archived.value
            case 'e': openDataFile
    elif e.key.number != None and e.action.keyup and not e.action.repeat:
        x = int(str(e.key))
        debug and ui.notify(f'{str(x)}: {table.rows[x-1].get("TBC")}')

def appResize(w: int, h: int):
    app.native.main_window.resize(w, h)

def customNotify(msg: str, group: str=None):
    if group == None:
        ui.notify(msg, position='top-right', timeout=2000, progress=True, close_button='×', badgeColor='primary')
    else:
        ui.notify(msg, position='top-right', timeout=2000, progress=True, close_button='×', group=group, badgeColor='primary')

def columnToggle(column: dict, visible: bool) -> None:
    column['classes'] = '' if visible else 'hidden'
    column['headerClasses'] = '' if visible else 'hidden'
    table.update()

# %% Setup table
# Process csv file to a list of dictionaries
with open(dataFile, newline='') as f:
    rows = [{k: int(v) if v.isnumeric() else v for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]
    
# Use first list item to generate columns
columns = [{'name': k, 'label': k, 'field': k, 'sortable': True, 'align': 'left'} for k in rows[0]]

# %% Create UI elements
edit = ui.button(on_click=openDataFile)
with edit:
    ui.tooltip('Edit source').props('anchor="top middle" self="bottom middle"')
    ui.icon('edit')

trim = ui.switch(value=True).props('checked-icon="content_cut" unchecked-icon="clear"')
with trim:
    ui.tooltip('Remove padding').props('anchor="top middle" self="bottom middle"')
    ui.html('<u>T</u>rim')

archived = ui.switch(value=False).props('checked-icon="update" unchecked-icon="clear"')
with archived:
    ui.tooltip('Hide archived').props('anchor="top middle" self="bottom middle"')
    ui.html('<u>A</u>rchived')

# QTable doesn't support cell events natively, requires custom on-click event
table = ui.table(columns=columns, rows=rows, pagination=9
    ).props('dense hide-pagination').classes('w-full')
table.add_slot('body', r'''
    <q-tr :props="props">
        <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            @click="$parent.$emit('cellClick', {row: props.row, col: col.name})"
        >
            {{ col.value }}  
        </q-td>
    </q-tr>
''')
table.on('cellClick', lambda cell: writeToClipboard(cell.args['row'][cell.args['col']]))

columnMenu = ui.button(icon='visibility')
with columnMenu:
    ui.tooltip('Show/hide fields').props('anchor="top middle" self="bottom middle"')
    with ui.menu().props('anchor="bottom right" self="top right"'), ui.column().classes('gap-0 p-2'):
        for column in columns:
            ui.switch(column['label'], value=True, on_change=lambda e, column=column: columnToggle(column, e.value))

filter = ui.input(label='', placeholder='Name or reference',
    ).bind_value_to(table, 'filter').props('clearable autofocus').classes('w-full')
with filter.add_slot('label'):
    ui.html('<b>F</b>ilter')

# %% Arrange UI elements
containerHeader = ui.row().classes('w-full')
filter.move(containerHeader)
containerBody = ui.element().classes('w-full h-72')
table.move(containerBody)

controlsFooter = ui.row().classes('w-full')
trim.move(controlsFooter)
archived.move(controlsFooter)
ui.space().move(controlsFooter)
edit.move(controlsFooter)
columnMenu.move(controlsFooter)

filter.set_autocomplete([e['name'] for e in rows])  # Must set *after* any .move() - ???

# Add focus tracking for keyboard events
focus = {'filter': False}
filter.on('focus', lambda e: focus.update({'filter': True}))
filter.on('focusout', lambda e: focus.update({'filter': False}))

# %% Run native app
# app.native.window_args['x'] = 
# app.native.window_args['y'] = 
# app.native.window_args['screen'] = webview.screens
app.native.window_args['resizable'] = False
app.native.window_args['on_top'] = True
app.native.start_args['debug'] = debug
# app.native.start_args['server_args'] = {'IsBrowserAcceleratorKeyEnabled': False}
app.native.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False

keyboard = ui.keyboard(on_key=handleKey, ignore=[])

# Add custom body size emitter, resize on launch
ui.add_head_html('''
    <script>
    function emitSize() {
        emitEvent('resize', {
            width: document.body.offsetWidth,
            height: document.body.offsetHeight,
        });
    }
    window.onload = emitSize;
    window.onresize = emitSize;
    </script>
''')
ui.on('resize', lambda e: appResize(e.args['width'], e.args['height']))

ui.run(title='Referencer', native=True, window_size=(500, 500), fullscreen=False, frameless=True, reload=debug)
customNotify('Debug mode' if debug else f'{len(rows)} loaded')