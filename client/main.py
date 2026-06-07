from kivy.config import Config
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

import sys
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from widgets import CardGame
from screens import (
    LobbyScreen, MenuScreen, GameScreen, ConstructionScreen,
    PlayScreen, MultiplayerConfigScreen, GameConfigScreen
)

# Parse --debug flag (default False). Usage examples:
#  python main.py --debug true
#  python main.py --debug=true
#  python main.py --debug
DEBUG_MODE = False
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == '--debug':
        # If next arg says true/1/yes treat as True, otherwise default to True when flag present
        if i + 1 < len(args) and args[i + 1].lower() in ('true', '1', 'yes'):
            DEBUG_MODE = True
        else:
            DEBUG_MODE = True
        break
    if a.startswith('--debug='):
        v = a.split('=', 1)[1]
        if v.lower() in ('true', '1', 'yes'):
            DEBUG_MODE = True
        break

print(f"[App] argv={sys.argv} parsed DEBUG_MODE={DEBUG_MODE}")
# Fallback: some launchers pass a lone 'true' as the single arg (no --debug).
if not DEBUG_MODE and any(a.lower() in ('true', '1', 'yes') for a in args):
    DEBUG_MODE = True
    print(f"[App] Detected bare true in argv, setting DEBUG_MODE=True")

# Load KV file
Builder.load_file(os.path.join(os.path.dirname(__file__), 'kv', 'cardgame.kv'))


class CardGameApp(App):
    kv_directory = os.path.join(os.path.dirname(__file__), 'kv')
    # def update(self, dt):
    #     # Solo actualiza si estamos en la pantalla del juego
    #     if self.root.current == "game":
    #         game_screen = self.root.get_screen("game")
    #         # game_screen.ids.card_game.check_if_painting()

    def build(self):
        # expose debug mode on the App instance
        self.debug_mode = DEBUG_MODE
        print(f"[App] debug_mode={self.debug_mode}")
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(ConstructionScreen(name="construction"))
        sm.add_widget(PlayScreen(name="play"))
        sm.add_widget(GameConfigScreen(name="game_config"))
        sm.add_widget(MultiplayerConfigScreen(name="multiplayer_config"))
        sm.add_widget(LobbyScreen(name="lobby"))
        # sm.add_widget(CustomScreen(name="custom"))

        # Clock.schedule_interval(self.update, 1)
        return sm

    # def paint_card(self, *args):
    #     game_screen = self.root.get_screen("game")
    #     card = game_screen.ids.card_game.ids.get("card")
    #     if card:
    #         if not card.painting:
    #                 card.painting = True
    #                 card.paint()
    #         else:
    #             card.painting = False

    # def clear_card(self, *args):
    #     game_screen = self.root.get_screen("game")
    #     card = game_screen.ids.card_game.ids.get("card")
    #     if card:
    #         card.clear_paint()

    # def save_card_image(self, *args):
    #     game_screen = self.root.get_screen("game")
    #     card = game_screen.ids.card_game.ids.get("card")
    #     if card:
    #         card.save_as_image("assets/mi_carta.png")

    # def load_card_image(self, *args):
    #     game_screen = self.root.get_screen("game")
    #     card = game_screen.ids.card_game.ids.get("card")
    #     if card:

    #         if not card.painting:
    #             card.painting = True
    #             card.paint()

    #         card.load_image("assets/mi_carta.png")


if __name__ == "__main__":
    CardGameApp().run()
