import pygame
from Card import Suite  

width, height = 1920, 1080

class Player():

    def __init__(self):
        self.cards = pygame.sprite.Group()
        self.scored_cards = pygame.sprite.Group()
        self.name = "Jugador"
        self.scored = False
        self.broom = 0

    def reposition_player_cards(self):
        n = self.cards.__len__()
        for card, i in zip(self.cards, range(1, n+1)):
            if not card.is_dragging():
                card.rect.center = (i*width//(n+1), 4*height//5)
                # print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}, posicion {card.rect.center}, i {i}")

    def golds(self):
        golds = 0
        for card in self.scored_cards:
            if card.suite.value == "GOLD":
                golds+=1
        return golds
    
    def sevens(self):
        sevens = 0
        for card in self.scored_cards:
            if card.value == 7:
                sevens+=1
        return sevens
    
    def has_golden_seven(self):
        for card in self.scored_cards:
            if card.value == 7 and card.suite.value == "GOLD":
                return True
        return False
    
    def reset(self):
        self.cards.empty()
        self.scored_cards.empty()
        self.scored = False
        self.broom = 0