from quart import Quart, websocket
from main import get_face_encoder, get_models, get_cap, run
import json

app = Quart(__name__)

@app.route('/')
async def hello():
    return 'hello'

@app.websocket('/ws')
async def ws():
    face_encoder = get_face_encoder()
    models = get_models()
    cap = get_cap()
    # async for message in websocket:
    while True:
        persons = list(run(cap, face_encoder, models, 2, 'large'))
        await websocket.send(json.dumps(persons))

app.run()