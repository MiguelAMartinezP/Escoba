import asyncio
import json
from typing import Dict, List

import websockets


class MultiplayerServer:
    """WebSocket server managing multiplayer lobbies."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.rooms: Dict[str, List[Dict[str, any]]] = {}

    async def handler(self, websocket):
        current_room = None

        try:
            async for message in websocket:
                data = json.loads(message)

                msg_type = data.get("type")
                room_id = str(data.get("room"))
                player_name = data.get("player_name", "Unknown")

                if msg_type == "create_lobby":
                    current_room = await self.create_lobby(websocket, room_id, player_name)

                elif msg_type == "join_lobby":
                    current_room = await self.join_lobby(websocket, room_id, player_name)

                else:
                    await self.broadcast(current_room, message, sender=websocket)

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:
            await self.disconnect(websocket, current_room)

    async def create_lobby(self, websocket, room_id: str, player_name: str) -> str:
        if room_id in self.rooms:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "La sala ya existe"
            }))
            return None

        self.rooms[room_id] = [{"websocket": websocket, "name": player_name}]

        await websocket.send(json.dumps({
            "type": "lobby_created",
            "room": room_id
        }))

        print(f"[SERVER] Sala creada: {room_id} por {player_name}")
        return room_id

    async def join_lobby(self, websocket, room_id: str, player_name: str) -> str:
        if room_id not in self.rooms:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "La sala no existe"
            }))
            return None

        self.rooms[room_id].append({"websocket": websocket, "name": player_name})

        await websocket.send(json.dumps({
            "type": "lobby_joined",
            "room": room_id
        }))

        # Notificar al resto
        await self.broadcast(room_id, json.dumps({
            "type": "player_joined",
            "player_name": player_name
        }), sender=websocket)

        print(f"[SERVER] {player_name} se unió a sala: {room_id}")
        return room_id

    async def broadcast(self, room_id: str, message: str, sender=None):
        if not room_id or room_id not in self.rooms:
            return

        for player_info in self.rooms[room_id]:
            client = player_info["websocket"]
            if client != sender:
                try:
                    await client.send(message)
                except:
                    pass

    async def disconnect(self, websocket, room_id: str):
        if not room_id or room_id not in self.rooms:
            return

        # Find and remove the player
        player_name = None
        for i, player_info in enumerate(self.rooms[room_id]):
            if player_info["websocket"] == websocket:
                player_name = player_info["name"]
                self.rooms[room_id].pop(i)
                break

        # Notificar salida con el nombre del jugador
        if player_name:
            await self.broadcast(room_id, json.dumps({
                "type": "player_left",
                "player_name": player_name
            }))

        if len(self.rooms[room_id]) == 0:
            del self.rooms[room_id]
            print(f"[SERVER] Sala eliminada: {room_id}")
        else:
            print(f"[SERVER] {player_name} salió de sala: {room_id}")

    async def start(self):
        print(f"[SERVER] Iniciando en ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()


if __name__ == "__main__":
    server = MultiplayerServer()
    asyncio.run(server.start())