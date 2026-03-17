from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, PushMatrix, PopMatrix, Translate
from kivy.graphics import Fbo, ClearColor, ClearBuffers, Rectangle
from kivy.core.image import Image as CoreImage
import os


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
