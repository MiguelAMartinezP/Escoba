from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.animation import Animation


class TableArea(Widget):
    opacity_value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_animation()

    def start_animation(self):
        anim = Animation(opacity_value=0.3, duration=1) + Animation(opacity_value=0.1, duration=1)
        anim.repeat = True
        anim.start(self)
