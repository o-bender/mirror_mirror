from quart import Quart, websocket, render_template
from quart.helpers import make_response
from main import get_models, get_cap, run
import json
from config import Config


app = Quart(__name__)
app.config.from_object(Config)


@app.route('/')
async def hello():
    template = await render_template('index.html')
    response = await make_response(template)
    response.set_cookie('city_id', app.config['CITY_ID'])
    response.set_cookie('ow_api_token', app.config['OPEN_WEATHE_API_TOKEN'])
    return response


def get_motion_sensor_status():
    return True


@app.websocket('/ws')
async def ws():
    models = get_models()
    cap = get_cap()
    # async for message in websocket:
    while True:
        if get_motion_sensor_status():
            persons = list(run(cap, models, 2, 'large'))
            await websocket.send(json.dumps(persons))

app.run()