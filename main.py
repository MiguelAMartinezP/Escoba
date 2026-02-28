from kivy.config import Config
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.animation import Animation
from kivy.clock import Clock


class TableArea(Widget):
    opacity_value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_animation()

    def start_animation(self):
        anim = Animation(opacity_value=0.5, duration=1) + Animation(opacity_value=0.1, duration=1)
        anim.repeat = True
        anim.start(self)


class Card(Widget):
    dragging = False
    touch_offset = ListProperty([0, 0])
    scale = NumericProperty(1.0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragging = True
            self.touch_offset = [self.x - touch.x, self.y - touch.y]
            self.animate_click_feedback()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            self.x = touch.x + self.touch_offset[0]
            self.y = touch.y + self.touch_offset[1]
            self.parent.check_table_area_visibility()

    def on_touch_up(self, touch):
        self.dragging = False
        self.parent.check_table_area_visibility()

        # Verificar si está dentro del área de la mesa
        table_area = self.parent.ids.table_area
        if table_area.collide_point(self.center_x, self.center_y):
            self.animate_snap_to_table(table_area)
        else:
            self.animate_fall()

        return super().on_touch_up(touch)

    def animate_click_feedback(self):
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
        anim = Animation(x=center_x, y=center_y, t='out_back', duration=0.3)
        anim.start(self)


class CardGame(Widget):
    def check_table_area_visibility(self):
        any_above_and_dragging = any(
            card.center_y > self.height / 3 and card.dragging
            for card in self.children
            if isinstance(card, Card)
        )
        self.ids.table_area.opacity = 1 if any_above_and_dragging else 0


class CardGameApp(App):
    def build(self):
        return CardGame()


if __name__ == "__main__":
    CardGameApp().run()
