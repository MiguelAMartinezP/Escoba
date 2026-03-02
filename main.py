from kivy.config import Config
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.graphics import Color, Line, PushMatrix, PopMatrix, Translate
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Fbo, ClearColor, ClearBuffers
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.graphics import Rectangle
from kivy.uix.recycleview import RecycleView
import os



class TableArea(Widget):
    opacity_value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_animation()

    def start_animation(self):
        anim = Animation(opacity_value=0.3, duration=1) + Animation(opacity_value=0.1, duration=1)
        anim.repeat = True
        anim.start(self)

class MyPaintWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lines = []  # ← Aquí guardaremos las líneas completas

        with self.canvas.before:
            PushMatrix()
            self.translate = Translate(self.x, self.y)
        with self.canvas.after:
            PopMatrix()
        self.bind(pos=self.update_transform)

    def update_transform(self, *args):
        if self.translate:
            self.translate.xy = self.pos

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        local = self.to_widget(*touch.pos, relative=True)
        with self.canvas:
            Color(1, 0, 0)
            line = Line(points=[local[0], local[1]])
            touch.ud['line'] = line
            self.lines.append(line)  # ← Guardamos la línea entera
        return True

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        local = self.to_widget(*touch.pos, relative=True)
        touch.ud['line'].points += [local[0], local[1]]
        return True

    def clear_drawing(self):
        self.canvas.clear()



class Card(Widget):
    dragging = False
    painting = False
    paint_widget = None
    touch_offset = ListProperty([0, 0])
    scale = NumericProperty(1.0)

    def on_touch_down(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            if self.collide_point(*touch.pos):
                return self.paint_widget.on_touch_down(touch)

        if self.collide_point(*touch.pos):
            self.dragging = True
            self.touch_offset = [self.x - touch.x, self.y - touch.y]
            self.animate_click_feedback()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            return self.paint_widget.on_touch_move(touch)

        if self.dragging:
            self.x = touch.x + self.touch_offset[0]
            self.y = touch.y + self.touch_offset[1]
            self.parent.check_table_area_visibility()
            self._update_paint_widget()

    def on_touch_up(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            return self.paint_widget.on_touch_up(touch)

        if self.collide_point(*touch.pos):
            self.dragging = False
            self.parent.check_table_area_visibility()
            table_area = self.parent.ids.table_area
            if table_area.collide_point(self.center_x, self.center_y):
                self.animate_snap_to_table(table_area)
            else:
                self.animate_fall()
        return super().on_touch_up(touch)

    def animate_click_feedback(self):
        # Animación: agranda y vuelve a su tamaño
        anim1 = Animation(scale=1.25, duration=0.1)
        anim2 = Animation(scale=1.0, duration=0.1)
        anim = anim1 + anim2
        anim.start(self)
    
    def animate_fall(self):
        anim1 = Animation(scale=0.75, duration=0.1)
        anim2 = Animation(scale=1.0, duration=0.1)
        anim = anim1 + anim2
        anim.start(self)
    
    def animate_snap_to_table(self, table_area):
        center_x = table_area.center_x - self.width / 2
        center_y = table_area.center_y - self.height / 2

        def update_widget(*args):
            self._update_paint_widget()

        anim = Animation(x=center_x, y=center_y, t='out_back', duration=0.3)
        anim.bind(on_progress=lambda *args: update_widget())
        anim.start(self)

    def paint(self):
        if not self.paint_widget:
            self.paint_widget = MyPaintWidget()
            self.add_widget(self.paint_widget)
            self.paint_widget.size = self.size
            self.paint_widget.pos = self.pos

    def _update_paint_widget(self, *args):
        if self.paint_widget:
            self.paint_widget.size = self.size
            self.paint_widget.pos = self.pos

    def clear_paint(self):
        if self.paint_widget:
            self.paint_widget.clear_drawing()

    def save_as_image(self, filename="carta.png"):
        if not self.paint_widget:
            print("No hay pintura para guardar.")
            return
        
        fbo = Fbo(size=self.paint_widget.size)

        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            PushMatrix()
            Translate(-self.paint_widget.x, -self.paint_widget.y)
            fbo.add(self.paint_widget.canvas)
            PopMatrix()

        fbo.draw()
        fbo.texture.save(filename)
        print(f"Guardado en {os.path.abspath(filename)}")


    def load_image(self, filepath):
        if not os.path.exists(filepath):
            print("Archivo no encontrado:", filepath)
            return

        texture = CoreImage(filepath, ext='png', nocache=True).texture

        with self.paint_widget.canvas:
            Rectangle(texture=texture, pos=(0,0), size=self.paint_widget.size)
        
        print("Dibujo cargado desde", filepath)
        self.painting = False


class CardGame(Widget):
    def check_table_area_visibility(self):
        # Mostramos el área si alguna carta está arriba de height/3
        any_above = any((card.center_y > self.height / 3 and card.dragging) for card in self.children if isinstance(card, Card))
        if any_above:
            self.ids.table_area.opacity = 1
        else:
            self.ids.table_area.opacity = 0

    def check_if_painting(self):
        card = self.ids.get("card")
        if card and card.painting:
            card.paint()


class CartaGrid(RecycleView):
    cartas = [{"valor": v, "palo": p} for v in ["As","2","3","4","5","6","7","Sota","Reina","Rey"]
                                for p in ["Oros","Copas","Espadas","Bastos"]]

    def mostrar_filtro(self, valor, palo):
        print("Filtrando")
        print("VALOR ", valor)
        print("PALO ", palo)
        if valor == "Selecciona un valor":
            valor = ""
        if palo == "Selecciona un palo":
            palo = ""

        if valor and palo:
            print("BOTH")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["valor"] == valor and c["palo"] == palo]
        elif valor:
            print("VALUE")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["valor"] == valor]
        elif palo:
            print("PLAO")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} 
                         for c in self.cartas if c["palo"] == palo]
        else:
            print("NADa")
            self.data = [{"text": f"{c['valor']} de {c['palo']}"} for c in self.cartas]


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

class CardGameApp(App):
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
