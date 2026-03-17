from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty
from kivy.animation import Animation
from kivy.graphics import Fbo, ClearColor, ClearBuffers, PushMatrix, PopMatrix, Translate, Rectangle
from kivy.core.image import Image as CoreImage
import os

from .paint_widget import MyPaintWidget


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
