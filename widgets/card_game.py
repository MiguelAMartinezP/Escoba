from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.properties import ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle

from .card import Card


from .card import Card


def get_card_image_path(card_str, show_back=False):
    """Convert card string to image path."""
    if show_back:
        return "assets/spanish_deck/BACK.PNG"
    
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


class CardDisplay(Widget):
    """A card display with image and optional label."""
    show_back = BooleanProperty(True)
    
    def __init__(self, card_str, is_selectable=False, show_back=False, show_label=False, **kwargs):
        super().__init__(**kwargs)
        self.card_str = card_str
        self.is_selectable = is_selectable
        self.selected = False
        self.show_back = show_back
        self.show_label = show_label
        
        # Card background for selection
        with self.canvas.before:
            Color(0.2, 0.5, 0.2, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Card image - no size_hint so manual sizing works
        self.card_image = Image(
            source=get_card_image_path(card_str, show_back),
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(self.card_image)
        
        # Optional label (for bot cards)
        if show_label:
            self.label = Label(text=card_str, font_size='10sp')
            self.add_widget(self.label)
        
        # Trigger initial update
        self.bind(size=self._update_bg, show_back=self._update_image)
    
    def _update_image(self, *args):
        """Update the card image when show_back changes."""
        self.card_image.source = get_card_image_path(self.card_str, self.show_back)
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        # Update image size - scaled 1.3x to make texture appear zoomed in
        scale_factor = 1
        scaled_width = self.width * scale_factor
        scaled_height = self.height * scale_factor
        offset_x = (self.width - scaled_width) / 2
        offset_y = (self.height - scaled_height) / 2
        self.card_image.size = (scaled_width, scaled_height)
        self.card_image.pos = (self.x + offset_x, self.y + offset_y)
        # Update label if exists - position below the card
        if hasattr(self, 'label'):
            label_height = 30
            # Position label below card (y axis is relative to parent, so negative to go below)
            self.label.pos = (self.x, self.y - label_height)
            self.label.size = (self.width, label_height)
    
    def on_touch_down(self, touch):
        if self.is_selectable and self.collide_point(*touch.pos):
            self.selected = not self.selected
            self._update_color()
            return True
        return super().on_touch_down(touch)
    
    def _update_color(self):
        color = (1, 1, 0, 1) if self.selected else (0.2, 0.5, 0.2, 1)  # Yellow if selected
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])


class CardGame(Widget):
    human_cards = ListProperty([])
    bot_cards = ListProperty([])
    table_cards = ListProperty([])
    human_turn = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.card_widgets = []
        self.bot_card_widgets = []
        self.table_card_widgets = []

    def update_hands(self, human_hand, bot_hand, human_turn=True):
        print(f"\n[UPDATE_HANDS] Human cards: {human_hand}")
        print(f"[UPDATE_HANDS] Bot cards: {bot_hand}")
        print(f"[UPDATE_HANDS] Human turn: {human_turn}")
        self.human_cards = human_hand
        self.bot_cards = bot_hand
        self.human_turn = human_turn
        self._create_card_widgets()
        self._update_card_interaction()

    def update_table(self, table_cards):
        print(f"[UPDATE_TABLE] Table cards: {table_cards}")
        self.table_cards = table_cards
        self._update_table_cards()

    def get_selected_table_cards(self):
        """Return list of selected table card strings."""
        return [card.card_str for card in self.table_card_widgets if card.selected]

    def clear_selections(self):
        """Clear all table card selections."""
        for card_widget in self.table_card_widgets:
            card_widget.selected = False
            card_widget._update_color()

    def highlight_bot_move(self, played_card_str, captured_card_strs):
        """Highlight the bot's played card and captured cards."""
        # Highlight played card from bot's hand
        for card_widget in self.bot_card_widgets:
            if card_widget.card_str == played_card_str:
                # Temporarily show the card face up and highlight it
                card_widget.show_back = False
                card_widget._update_color()  # This will show it as "selected"
                break
        
        # Highlight captured cards on table
        for card_widget in self.table_card_widgets:
            if card_widget.card_str in captured_card_strs:
                card_widget.selected = True
                card_widget._update_color()
    
    def clear_bot_highlights(self):
        """Clear all bot highlights."""
        # Hide bot's played card again and reset selection
        for card_widget in self.bot_card_widgets:
            card_widget.show_back = True
            card_widget.selected = False
            card_widget._update_color()
        
        # Clear table card highlights
        for card_widget in self.table_card_widgets:
            card_widget.selected = False
            card_widget._update_color()

    def _create_card_widgets(self):
        # Clear existing human cards
        for card in self.card_widgets:
            if card in self.children:
                self.remove_widget(card)
        self.card_widgets = []

        # Create cards for human hand (bottom) - using actual Card widgets for interaction
        print(f"[CREATE_WIDGETS] Creating {len(self.human_cards)} card widgets")
        for i, card_str in enumerate(self.human_cards):
            print(f"[CREATE_WIDGETS] Widget {i}: {card_str}")
            card = Card()
            card.size_hint = (None, None)
            card.size = (200, 280)
            card.pos = ((180 + i * 240) * 2, 50)
            card.card_str = card_str
            card.human_turn = self.human_turn
            self.add_widget(card)
            self.card_widgets.append(card)

        # Create cards for bot hand (top)
        self._update_bot_cards()
        
        # Create cards for table (middle)
        self._update_table_cards()

    def _update_card_interaction(self):
        """Update the human_turn property on all human cards."""
        for card in self.card_widgets:
            card.human_turn = self.human_turn

    def _update_bot_cards(self):
        # Clear existing bot cards
        for card in self.bot_card_widgets:
            if card in self.children:
                self.remove_widget(card)
        self.bot_card_widgets = []

        # Create cards for bot hand (top of screen)
        for i, card_str in enumerate(self.bot_cards):
            card_display = CardDisplay(card_str, is_selectable=False, show_back=True, show_label=True)
            card_display.size_hint = (None, None)
            card_display.size = (100, 140)
            card_display.pos = ((650 + i * 240), self.height - 190)
            self.add_widget(card_display)
            self.bot_card_widgets.append(card_display)

    def _update_table_cards(self):
        # Clear existing table cards
        for card in self.table_card_widgets:
            if card in self.children:
                self.remove_widget(card)
        self.table_card_widgets = []

        # Create cards for table (middle of screen) - 1.5x size, centered
        card_width = 150
        card_height = 210
        spacing = 20
        
        # Calculate total width needed
        num_cards = len(self.table_cards)
        total_width = num_cards * card_width + (num_cards - 1) * spacing
        
        # Center horizontally
        start_x = (self.width - total_width) / 2
        center_y = self.height // 2 - card_height // 2
        
        for i, card_str in enumerate(self.table_cards):
            card_display = CardDisplay(card_str, is_selectable=True, show_back=False, show_label=False)
            card_display.size_hint = (None, None)
            card_display.size = (card_width, card_height)
            card_display.pos = (start_x + i * (card_width + spacing), center_y)
            self.add_widget(card_display)
            self.table_card_widgets.append(card_display)

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
