from kivy.uix.widget import Widget

from .card import Card


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
