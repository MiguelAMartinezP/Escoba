import asyncio
import json

import pytest
import websockets
import importlib.util
from pathlib import Path

# Load server module directly from file to avoid package/import issues
server_path = Path(__file__).resolve().parent / "server.py"
spec = importlib.util.spec_from_file_location("mult_server", str(server_path))
server_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_mod)
MultiplayerServer = server_mod.MultiplayerServer


@pytest.fixture(scope="module")
def ws_server():
    import threading

    srv = MultiplayerServer(host="127.0.0.1", port=8081)
    ready = threading.Event()
    loop_container = {}

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stop = asyncio.Event()

        async def _run():
            server = await websockets.serve(srv.handler, srv.host, srv.port)
            loop_container['loop'] = loop
            loop_container['server'] = server
            loop_container['stop'] = stop
            ready.set()
            await stop.wait()
            server.close()
            await server.wait_closed()

        loop.run_until_complete(_run())
        loop.close()

    t = threading.Thread(target=thread_target, daemon=True)
    t.start()
    ready.wait(timeout=1)
    yield srv
    loop = loop_container.get('loop')
    stop = loop_container.get('stop')
    if loop and stop:
        loop.call_soon_threadsafe(stop.set)
    t.join(timeout=1)


@pytest.mark.asyncio
async def test_create_and_join_lobby(ws_server):
    uri = "ws://127.0.0.1:8081"

    async with websockets.connect(uri) as ws1:
        # create lobby
        await ws1.send(json.dumps({"type": "create_lobby", "room": "r1", "player_name": "Alice"}))
        msg = json.loads(await ws1.recv())
        assert msg.get("type") == "lobby_created"
        assert msg.get("room") == "r1"

        # connect second client
        async with websockets.connect(uri) as ws2:
            await ws2.send(json.dumps({"type": "join_lobby", "room": "r1", "player_name": "Bob"}))

            # ws2 should receive lobby_joined
            msg2 = json.loads(await ws2.recv())
            assert msg2.get("type") == "lobby_joined"

            # ws1 should receive player_joined broadcast
            joined = json.loads(await ws1.recv())
            assert joined.get("type") == "player_joined"
            assert joined.get("player_name") == "Bob"


@pytest.mark.asyncio
async def test_broadcast_and_disconnect(ws_server):
    uri = "ws://127.0.0.1:8081"

    async with websockets.connect(uri) as ws1:
        await ws1.send(json.dumps({"type": "create_lobby", "room": "r2", "player_name": "A"}))
        _ = json.loads(await ws1.recv())

        async with websockets.connect(uri) as ws2:
            await ws2.send(json.dumps({"type": "join_lobby", "room": "r2", "player_name": "B"}))
            _ = json.loads(await ws2.recv())
            # ws1 gets joined
            _ = json.loads(await ws1.recv())

            # Now close ws2 to trigger disconnect notification
        # after exiting inner context ws2 is closed; give server time to broadcast
        await asyncio.sleep(0.1)

        # ws1 should receive player_left
        left = json.loads(await ws1.recv())
        assert left.get("type") == "player_left"
        assert left.get("player_name") == "B"
