import asyncio
import json
import random
import string

import pytest
import websockets


async def _try_connect(ports=(8081, 8080), timeout=0.5):
    """Try connecting to a list of ports, return connected websocket and uri or (None, None)."""
    for port in ports:
        uri = f"ws://127.0.0.1:{port}"
        try:
            ws = await asyncio.wait_for(websockets.connect(uri), timeout=timeout)
            return ws, uri
        except Exception:
            continue
    return None, None


def _random_room():
    return "test-" + "".join(random.choice(string.ascii_lowercase) for _ in range(6))


@pytest.mark.asyncio
async def test_client_create_lobby_and_receive_response():
    ws, uri = await _try_connect()
    if not ws:
        pytest.skip("No websocket server reachable on 8081 or 8080")

    room = _random_room()
    try:
        await ws.send(json.dumps({"type": "create_lobby", "room": room, "player_name": "pyclient"}))
        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
        data = json.loads(msg)
        assert data.get("type") == "lobby_created"
        assert data.get("room") == room
    finally:
        await ws.close()


@pytest.mark.asyncio
async def test_client_join_and_receive_broadcast():
    # Need two clients; skip if server unreachable
    ws1, uri = await _try_connect()
    if not ws1:
        pytest.skip("No websocket server reachable on 8081 or 8080")

    ws2 = None
    try:
        ws2 = await websockets.connect(uri)
        room = _random_room()

        # create lobby with ws1
        await ws1.send(json.dumps({"type": "create_lobby", "room": room, "player_name": "creator"}))
        _ = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))

        # join with ws2
        await ws2.send(json.dumps({"type": "join_lobby", "room": room, "player_name": "joiner"}))
        # ws2 should receive lobby_joined
        msg2 = json.loads(await asyncio.wait_for(ws2.recv(), timeout=1.0))
        assert msg2.get("type") == "lobby_joined"

        # ws1 should receive player_joined broadcast
        joined = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))
        assert joined.get("type") == "player_joined"
        assert joined.get("player_name") == "joiner"

    finally:
        await ws1.close()
        if ws2:
            await ws2.close()


@pytest.mark.asyncio
async def test_game_init_broadcast():
    ws1, uri = await _try_connect()
    if not ws1:
        pytest.skip("No websocket server reachable on 8081 or 8080")

    ws2 = None
    try:
        ws2 = await websockets.connect(uri)
        room = _random_room()

        # create and join
        await ws1.send(json.dumps({"type": "create_lobby", "room": room, "player_name": "creator"}))
        _ = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))
        await ws2.send(json.dumps({"type": "join_lobby", "room": room, "player_name": "joiner"}))
        _ = json.loads(await asyncio.wait_for(ws2.recv(), timeout=1.0))
        _ = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))

        # simplified game_init message
        game_init = {
            "type": "game_init",
            "players": [
                {"name": "creator", "hand": ["4 de copas", "10 de copas", "11 de copas"]},
                {"name": "joiner", "hand": ["10 de oros", "1 de bastos", "4 de oros"]}
            ],
            "table": ["12 de espadas", "4 de espadas", "2 de oros", "10 de espadas"],
            "current_player_index": 0
        }

        await ws1.send(json.dumps(game_init))
        received = json.loads(await asyncio.wait_for(ws2.recv(), timeout=1.0))
        assert received.get("type") == "game_init"
        assert isinstance(received.get("players"), list)
        assert isinstance(received.get("table"), list)
        assert isinstance(received.get("current_player_index"), int)

    finally:
        await ws1.close()
        if ws2:
            await ws2.close()


@pytest.mark.asyncio
async def test_play_turn_broadcast():
    ws1, uri = await _try_connect()
    if not ws1:
        pytest.skip("No websocket server reachable on 8081 or 8080")

    ws2 = None
    try:
        ws2 = await websockets.connect(uri)
        room = _random_room()

        # create and join
        await ws1.send(json.dumps({"type": "create_lobby", "room": room, "player_name": "creator"}))
        _ = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))
        await ws2.send(json.dumps({"type": "join_lobby", "room": room, "player_name": "joiner"}))
        _ = json.loads(await asyncio.wait_for(ws2.recv(), timeout=1.0))
        _ = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))

        # play_turn message example
        play_turn = {
            "type": "play_turn",
            "card": "11 de copas",
            "selected_table": ["4 de espadas", "2 de oros"]
        }

        await ws2.send(json.dumps(play_turn))
        rec = json.loads(await asyncio.wait_for(ws1.recv(), timeout=1.0))
        assert rec.get("type") == "play_turn"
        assert rec.get("card") == "11 de copas"
        assert rec.get("selected_table") == ["4 de espadas", "2 de oros"]
        
    finally:
        await ws1.close()
        if ws2:
            await ws2.close()
