import itertools
import random
import pygame

from Player import Player

width, height = 1920, 1080
clock = pygame.time.Clock()            #get a pygame clock object
clock.tick(60)                     #update 60 times per second

class Bot(Player):
    def __init__(self):
        super().__init__()
        self.name = "BOT"
        #self.dificulty

    def play(self, deck, screen):
        if self.cards:
            for card in self.cards:
                can_play, combo = self.can_score(card, deck.drawn_cards)
                if can_play:
                    combo = list(combo)
                    for table_card in deck.drawn_cards:
                        if table_card.value in combo:
                            print(f"{self.name} selecciona {table_card.value} de {table_card.suite}")
                            # table_card.image = pygame.image.load("assets/scaled_negativo.png")
                            table_card.select_card()
                            deck.drawn_cards.draw(screen)
                            pygame.display.flip()
                            pygame.time.delay(500)  # espera medio segundo (500 ms)
                            deck.drawn_cards.remove(table_card)
                            combo.remove(table_card.value)
                            self.scored_cards.add(table_card)
                    
                        
                    if card.value == 1 or (card.value in range(1, 9) and card.suite.value == "GOLD"):
                        card.image = pygame.image.load(f"assets/c{card.value}_{card.suite.value}_SCALED.png")
                    else:
                        card.image = pygame.image.load(f"assets/c{card.value}_{card.suite.value}.png")
                    self.cards.draw(screen)
                    pygame.display.flip()
                    pygame.time.delay(1000)  # espera medio segundo (500 ms)
                    self.cards.remove(card)
                    self.scored_cards.add(card)
                    self.scored = True
                    print(f"{self.name} juega {card.value} de {card.suite}")
                    if not deck.drawn_cards:
                        self.broom+=1
                    return

            cards_list = list(self.cards)
            random.shuffle(cards_list)
            played_card = cards_list[0]
            if played_card.value == 1 or (played_card.value in range(1, 9) and played_card.suite.value == "GOLD"):
                played_card.image = pygame.image.load(f"assets/c{played_card.value}_{played_card.suite.value}_SCALED.png")
            else:
                played_card.image = pygame.image.load(f"assets/c{played_card.value}_{played_card.suite.value}.png")
            self.cards.remove(played_card)
            deck.drawn_cards.add(played_card)
            print(f"{self.name} juega {card.value} de {card.suite}")


          
    def can_score(self, card, table_cards):
        values = []
        for c in table_cards:
            values.append(c.value)
        
        for r in range(1, len(values) + 1):
            for combo in itertools.combinations(values, r):
                if sum(combo) + card.value == 15:
                    return True, combo
        return False, None
    
    def reposition_bot_cards(self):
        n = self.cards.__len__()
        for card, i in zip(self.cards, range(1, n+1)):
            card.rect.center = (i*width//(n+1), height//5)

