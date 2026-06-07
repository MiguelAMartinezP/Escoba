import asyncio
import json
import threading
from typing import Callable, Optional
import random

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None


class MultiplayerClient:
    """Manages a websocket connection to a multiplayer game server."""

    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
        on_message: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.on_status = on_status
        self.on_message = on_message
        self.on_error = on_error
        self._message_handlers = []
        self._status_handlers = []
        self._error_handlers = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.websocket = None
        self.thread: Optional[threading.Thread] = None
        self.connected = False
        self._host = "localhost"
        self._port = 8080
        self._room = ""
        self._create_room = False
        self._waiting_for_lobby_response = False

    @staticmethod
    def format_uri(host: str, port: str) -> str:
        return f"ws://localhost:8080"

    def connect(self, create: bool = False, room: str = "", player_name: str = "") -> None:

        if self.thread and self.thread.is_alive():
            self._notify_status("Ya hay una conexión en curso")
            return

        if not room:
            room = str(random.randint(10000, 99999))

        self._room = room.strip()
        self._create_room = create
        self._player_name = player_name
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._notify_status("Iniciando conexión...")

    def disconnect(self) -> None:
        if self.connected and self.loop and self.websocket:
            self.loop.call_soon_threadsafe(asyncio.create_task, self.websocket.close())
            self._notify_status("Desconectando...")
        else:
            self._notify_status("No hay conexión activa")
        # Reset waiting flag
        self._waiting_for_lobby_response = False

    def send_game_message(self, payload: dict) -> None:
        if not self.connected or not self.loop or not self.websocket:
            self._notify_error("No conectado al servidor")
            return

        self.loop.call_soon_threadsafe(asyncio.create_task, self.websocket.send(json.dumps(payload)))

    def _run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect())
        except Exception as error:
            self._notify_error(f"Error de conexión: {error}")
        finally:
            self.connected = False
            self._notify_status("Conexión finalizada")
            self.loop.close()

    async def _connect(self) -> None:
        uri = self.format_uri(self._host, self._port)
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connected = True
                self._notify_status(f"Conectado a {uri}")
                await self._send_lobby_action()

                async for message in websocket:
                    self._notify_message(message)
        except asyncio.TimeoutError:
            self._notify_error("Tiempo de conexión agotado. No se pudo conectar al servidor.")
        except Exception as error:
            error_msg = str(error)
            if "Connect call failed" in error_msg or "ECONNREFUSED" in error_msg:
                self._notify_error("No se pudo conectar al servidor. Verifica que el servidor esté ejecutándose.")
            elif "Connection timed out" in error_msg:
                self._notify_error("Conexión expirada. El servidor no responde.")
            else:
                self._notify_error(f"Error de conexión: {error_msg}")
        finally:
            self.connected = False
            self._waiting_for_lobby_response = False

    async def _send_lobby_action(self) -> None:
        if not self._room:
            self._notify_status("Usa un nombre de sala válido")
            return

        self._waiting_for_lobby_response = True
        lobby_action = {
            "type": "create_lobby" if self._create_room else "join_lobby",
            "room": self._room,
            "player_name": self._player_name
        }
        await self.websocket.send(json.dumps(lobby_action))
        self._notify_status(
            "Creando sala..." if self._create_room else "Uniéndose a la sala..."
        )

    def add_message_handler(self, handler):
        if callable(handler) and handler not in self._message_handlers:
            self._message_handlers.append(handler)

    def remove_message_handler(self, handler):
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    def add_status_handler(self, handler):
        if callable(handler) and handler not in self._status_handlers:
            self._status_handlers.append(handler)

    def remove_status_handler(self, handler):
        if handler in self._status_handlers:
            self._status_handlers.remove(handler)

    def add_error_handler(self, handler):
        if callable(handler) and handler not in self._error_handlers:
            self._error_handlers.append(handler)

    def remove_error_handler(self, handler):
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)

    def _notify_status(self, message: str) -> None:
        if callable(self.on_status):
            self.on_status(message)
        for handler in list(self._status_handlers):
            handler(message)

    def _notify_message(self, message: str) -> None:
        if callable(self.on_message):
            self.on_message(message)
        for handler in list(self._message_handlers):
            handler(message)
        
        # Check if this is a response to our lobby action
        if self._waiting_for_lobby_response:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                if msg_type in ["lobby_created", "lobby_joined"]:
                    # Success - clear waiting flag
                    self._waiting_for_lobby_response = False
                elif msg_type in ["error", "lobby_error", "create_failed", "join_failed"]:
                    # Server error - show it and clear waiting flag
                    error_msg = data.get("message", data.get("error", "Error del servidor"))
                    self._notify_error(f"Error: {error_msg}")
                    self._waiting_for_lobby_response = False
                # For other message types, keep waiting
            except json.JSONDecodeError:
                # If it's not JSON and we're waiting for lobby response, treat it as an error
                if self._waiting_for_lobby_response and message.strip():
                    self._notify_error(f"Error del servidor: {message}")
                    self._waiting_for_lobby_response = False

    def _notify_error(self, message: str) -> None:
        if callable(self.on_error):
            self.on_error(message)
        for handler in list(self._error_handlers):
            handler(message)
