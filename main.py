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
    webbrowser.open(f'{path}\{dataFile}')
    ui.notify('Opening file...')

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
            ui.notify('Cannot shutdown in debug mode')
        else:
            app.shutdown()
    elif isNumberKey(e.key) and e.action.keyup and not e.action.repeat:
        x = int(str(e.key))
        ui.notify(f'{str(x)}: {table.rows[x-1].get("primary")}')

# %% Setup table
columns = [
    {'name': 'id', 'label': '#', 'field': 'id', 'sortable': False, 'align': 'left'},
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
trim = ui.switch('Trim', value=True)

# QTable doesn't support cell events natively, requires custom on-click event
table = ui.table(columns=columns, rows=rows, row_key='id', pagination=9, on_select=lambda e: ui.notify('test')).props('dense').props('hide-pagination').classes('w-full')
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

filter = ui.input(label='Search', placeholder='name name',
    validation={'Input too long': lambda value: len(value) < 20}
    ).bind_value_to(table, 'filter').classes('w-2/4')

# %% Arrange UI elements
controls = ui.row().classes('w-full')
container = ui.element().classes('w-full')
filter.move(controls)
ui.space().move(controls)
trim.move(controls)
edit.move(controls)
controls.move(container)
table.move(container)
# if debug: ui.button('Resize', on_click=lambda: app.native.main_window.resize(500, 380))

# %% Run native app
app.native.window_args['resizable'] = False
app.native.start_args['debug'] = debug
app.native.settings['ALLOW_DOWNLOADS'] = True

keyboard = ui.keyboard(on_key=handleKey, ignore=[])

ui.run(title='Referencer', native=True, window_size=(500, 380), fullscreen=False, frameless=True, reload=debug)
if debug: ui.notify('Debug mode')