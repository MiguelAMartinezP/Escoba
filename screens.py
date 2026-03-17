from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty


class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    pass


class ConstructionScreen(Screen):
    pass


class PlayScreen(Screen):
    pass


class ConfigScreen(Screen):
    pass


class CustomScreen(Screen):
    valor_seleccionado = StringProperty("")
    palo_seleccionado = StringProperty("")

    def on_enter(self):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

    def on_valor_seleccionado(self, instance, value):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

    def on_palo_seleccionado(self, instance, value):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)