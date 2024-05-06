from nicegui import app, ui
from nicegui.events import KeyEventArguments
import csv
import inspect, os.path
import re
import webbrowser

debug = True

filename = inspect.getframeinfo(inspect.currentframe()).filename
path     = os.path.dirname(os.path.abspath(filename))
dataFile = 'data_sample.csv' if debug else 'data.csv'

# %% Definitions
def openDataFile():
    ui.notify('Opening file...')
    webbrowser.open(f'{path}\{dataFile}')

def writeToClipboard(text):
    if trim.value:
        # Replace any 0's in the middle of a string; https://regex101.com/r/5a5jxD/1
        output = re.sub(r'^(\D*)0*(\d+.*)', r'\1\2', text)
    else:
        output = text
        
    ui.clipboard.write(output)
    ui.notify(f'Copied \'{output}\'')

def isNumberKey(key):
    try:
        n = int(str(key))   
        return n > 0 and n < 10
    except:
        return False

def handleKey(e: KeyEventArguments):
    if e.key == 'Escape' and e.action.keydown:
        if debug:
            customNotify('Cannot shutdown in debug mode')
        else:
            app.shutdown()
    elif e.key == 's' and e.modifiers.ctrl and e.action.keydown:
        filter.run_method('focus')
    elif e.key == 't' and e.modifiers.ctrl and e.action.keydown:
        trim.value = not trim.value
    elif e.key == 'a' and e.modifiers.ctrl and e.action.keydown:
        archived.value = not archived.value
    elif e.key == 'e' and e.modifiers.ctrl and e.action.keydown:
        openDataFile
    elif isNumberKey(e.key) and e.action.keyup and not e.action.repeat:
        x = int(str(e.key))
        # if debug: ui.notify(f'{str(x)}: {table.rows[x-1].get("TBC")}')

def appResize(w: int, h: int):
    app.native.main_window.resize(w, h)

def customNotify(m: str):
    ui.notify(m, position='top-right', timeout=2000, progress=True, close_button='×')

# %% Setup table
columns = [
    {'name': 'id', 'label': '#', 'field': 'id', 'sortable': True, 'align': 'left'},
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'sortable': True, 'align': 'left'},
    {'name': 'a', 'label': 'A', 'field': 'a', 'sortable': True, 'align': 'left'},
    {'name': 'b', 'label': 'B', 'field': 'b', 'sortable': True, 'align': 'left'},
    {'name': 'c', 'label': 'C', 'field': 'c', 'sortable': True, 'align': 'left'}
]

rows = []
with open(dataFile, newline='') as data:
    contents = csv.DictReader(data)
    for row in contents:
        rows.append({'id': contents.line_num - 1, 'name': row['name'], 'a': row['a'], 'b': row['b'], 'c': row['c']})

# %% Create UI elements
edit = ui.button('Edit', on_click=openDataFile)
with edit:
    ui.tooltip('Edit source').props('anchor="center left"').props('self="center right"')

trim = ui.switch('Trim', value=True)
with trim:
    ui.tooltip('Remove padding').props('anchor="center right"').props('self="center left"').props(':offset="[140, 0]"')

if debug:   # Todo: implement
    archived = ui.switch('Archived', value=False)
    with archived:
        ui.tooltip('Hide archived').props('anchor="center right"').props('self="center left"')

# QTable doesn't support cell events natively, requires custom on-click event
table = ui.table(columns=columns, rows=rows, row_key='id', pagination=9
    ).props('dense').props('hide-pagination').classes('w-full')
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

names = [l['name'] for l in rows]
filter = ui.input(label='Search', placeholder='Name or reference',
    ).bind_value_to(table, 'filter').props('clearable').props('autofocus').classes('w-full')

# %% Arrange UI elements
containerBody = ui.element().classes('w-full').classes('h-72')
table.move(containerBody)

controlsFooter = ui.row().classes('w-full')
trim.move(controlsFooter)
archived.move(controlsFooter)
ui.space().move(controlsFooter)
edit.move(controlsFooter)

filter.set_autocomplete(names)  # Must set *after* any .move() - ???

# %% Run native app
app.native.window_args['resizable'] = False
app.native.start_args['debug'] = debug
app.native.settings['ALLOW_DOWNLOADS'] = True

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

ui.run(title='Referencer', native=True, window_size=(500, 445), fullscreen=False, frameless=True, reload=debug)
customNotify('Debug mode' if debug else f'{len(rows)} loaded')