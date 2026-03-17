from kivy.config import Config
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

import os
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from widgets import CardGame
from screens import (
    MenuScreen, GameScreen, ConstructionScreen,
    PlayScreen, ConfigScreen, CustomScreen
)


class CardGameApp(App):
    kv_directory = os.path.join(os.path.dirname(__file__), 'kv')
    def update(self, dt):
        # Solo actualiza si estamos en la pantalla del juego
        if self.root.current == "game":
            game_screen = self.root.get_screen("game")
            game_screen.ids.card_game.check_if_painting()

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(ConstructionScreen(name="construction"))
        sm.add_widget(PlayScreen(name="play"))
        sm.add_widget(ConfigScreen(name="config"))
        sm.add_widget(CustomScreen(name="custom"))

        Clock.schedule_interval(self.update, 1)
        return sm

    def paint_card(self, *args):
        game_screen = self.root.get_screen("game")
        card = game_screen.ids.card_game.ids.get("card")
        if card:
            if not card.painting:
                    card.painting = True
                    card.paint()
            else:
                card.painting = False

    def clear_card(self, *args):
        game_screen = self.root.get_screen("game")
        card = game_screen.ids.card_game.ids.get("card")
        if card:
            card.clear_paint()

    def save_card_image(self, *args):
        game_screen = self.root.get_screen("game")
        card = game_screen.ids.card_game.ids.get("card")
        if card:
            card.save_as_image("assets/mi_carta.png")

    def load_card_image(self, *args):
        game_screen = self.root.get_screen("game")
        card = game_screen.ids.card_game.ids.get("card")
        if card:

            if not card.painting:
                card.painting = True
                card.paint()

            card.load_image("assets/mi_carta.png")


if __name__ == "__main__":
    CardGameApp().run()
