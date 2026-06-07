from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.image import Image
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.animation import Animation
from kivy.graphics import Fbo, ClearColor, ClearBuffers, PushMatrix, PopMatrix, Translate, Rectangle
from kivy.core.image import Image as CoreImage
import os

from .paint_widget import MyPaintWidget


def get_card_image_path(card_str):
    """Convert card string to image path."""
    # Parse card string like "7 de espadas"
    parts = card_str.split(" de ")
    if len(parts) != 2:
        return "assets/spanish_deck/BACK.PNG"  # fallback
    
    rank_str, suit_str = parts
    rank = int(rank_str)
    
    # Map ranks: assets are 1-7 (numbered), 8 (jack/10), 9 (knight/11), 10 (king/12)
    if rank == 10:
        rank = 8  # Jack
    elif rank == 11:
        rank = 9  # Knight
    elif rank == 12:
        rank = 10  # King
    
    # Map Spanish suits to asset abbreviations
    suit_map = {
        "oros": "GOLD",
        "copas": "CUP", 
        "espadas": "SWORD",
        "bastos": "CLUB"
    }
    
    suit = suit_map.get(suit_str, "GOLD")  # fallback to GOLD
    
    return f"assets/spanish_deck/{rank}{suit}.PNG"


class Card(Widget):
    dragging = False
    painting = False
    paint_widget = None
    touch_offset = ListProperty([0, 0])
    scale = NumericProperty(1.0)
    card_str = StringProperty('')
    human_turn = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add card image - no size_hint so manual sizing works
        self.card_image = Image(
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.card_image)
        self.bind(size=self._update_image, pos=self._update_image, card_str=self._update_image)
        # Store original position when first positioned
        self._original_position_set = False

    def _update_image(self, *args):
        # Store original position on first positioning (when card is placed in hand)
        if not self._original_position_set and self.x != 0 and self.y != 0:
            self.original_x = self.x
            self.original_y = self.y
            self._original_position_set = True
        
        # Scale image 1.3x to make texture appear zoomed in
        scale_factor = 1
        scaled_width = self.width * scale_factor
        scaled_height = self.height * scale_factor
        offset_x = (self.width - scaled_width) / 2
        offset_y = (self.height - scaled_height) / 2
        self.card_image.size = (scaled_width, scaled_height)
        self.card_image.pos = (self.x + offset_x, self.y + offset_y)
        if self.card_str:
            self.card_image.source = get_card_image_path(self.card_str)

    def on_touch_down(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            if self.collide_point(*touch.pos):
                return self.paint_widget.on_touch_down(touch)

        if self.collide_point(*touch.pos) and self.human_turn:
            self.dragging = True
            self.touch_offset = [self.x - touch.x, self.y - touch.y]
            self.animate_click_feedback()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            return self.paint_widget.on_touch_move(touch)

        if self.dragging and self.human_turn:
            self.x = touch.x + self.touch_offset[0]
            self.y = touch.y + self.touch_offset[1]
            self.parent.check_table_area_visibility()
            self._update_paint_widget()

    def on_touch_up(self, touch):
        if self.painting and hasattr(self, 'paint_widget'):
            return self.paint_widget.on_touch_up(touch)

        if self.collide_point(*touch.pos) and self.human_turn:
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

        def on_complete(*args):
            # After snapping, play the card
            if hasattr(self, 'card_str'):
                success = self.parent.parent.play_card(self.card_str)  # parent.parent is GameScreen
                if not success:
                    # Play was invalid, animate back to original position
                    self.animate_return_to_hand()

        anim = Animation(x=center_x, y=center_y, t='out_back', duration=0.3)
        anim.bind(on_progress=lambda *args: update_widget())
        anim.bind(on_complete=on_complete)
        anim.start(self)

    def animate_return_to_hand(self):
        """Animate the card back to its original position in hand."""
        if hasattr(self, 'original_x') and hasattr(self, 'original_y'):
            anim = Animation(x=self.original_x, y=self.original_y, t='out_back', duration=0.3)
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
