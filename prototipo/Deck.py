import pygame
import random
from Card import Card, Suite

width, height = 1920, 1080

# Deck contains 44 Card objects to be drawn from
class Deck:
    
    def __init__(self):
        self.starting = True
        self.image = pygame.image.load(f"assets/scaled_negativo.png")
        self.image = pygame.transform.scale(self.image, (100, 150))
        self.rect = self.image.get_rect()
        self.rect.center = (150, 200)
        self.all_cards = []
        self.drawn_cards = pygame.sprite.Group()

        for i in range(1, 11):
            for s in Suite:
                if i == 1 or (i in range(1, 9) and s.value == "GOLD"):
                    print("SCALED")
                    c = Card(i, s, pygame.image.load(f"assets/c{i}_{s.value}_SCALED.png"), (0,0))
                    print(f"[DEBUG] CARTA OBTENIDA: valor {c.value}, palo {c.suite}")
                else:
                    c = Card(i, s, pygame.image.load(f"assets/c{i}_{s.value}.png"), (0,0))
                self.all_cards.append(c)

    def start(self):
        for i in range(1, 11):
            for s in Suite:
                if i == 1:
                    c = Card(i, s, pygame.image.load(f"assets/c{i}_{s.value}_SCALED.png"), (0,0))
                else:
                    c = Card(i, s, pygame.image.load(f"assets/c{i}_{s.value}.png"), (0,0))
                self.all_cards.append(c)
        self.shuffle()


    def shuffle(self):
        random.shuffle(self.all_cards)

    def deal(self):
        if self.starting:
            print("EMPESANDO")
            table = [self.all_cards.pop(0) for _ in range(4)]
            for item in table:
                self.drawn_cards.add(item)
                print(f"[DEBUG] CARTA OBTENIDA EN LA MESA: valor {item.value}, palo {item.suite}")

        
        return self.draw()

    
    def draw(self):
        j1 = [self.all_cards.pop(0) for _ in range(3)]
        j2 = [self.all_cards.pop(0) for _ in range(3)]

        return j1, j2
    
    def draw_one(self):
        self.drawn_cards.add(self.all_cards.pop(0))

        for card in self.drawn_cards:
            print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
        
        return
    
    def draw_player(self):
        card = self.all_cards.pop(0)
        
        print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
        
        return card
        
    
    def reposition_deck_cards(self):
        n = self.drawn_cards.__len__()
        for card, i in zip(self.drawn_cards, range(1, n+1)):
            # print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}, posicion {card.rect.center}, i {i}")
            if card.selected:
                card.rect.center = (i*width//(n+1), (height//2)-30)
            else:
                card.rect.center = (i*width//(n+1), height//2)