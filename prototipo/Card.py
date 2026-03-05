import pygame
from enum import Enum

class Suite(Enum):
    GOLD = "GOLD"
    CUP = "CUP"
    SWORD = "SWORD"
    CLUB = "CLUB"

class Card(pygame.sprite.Sprite):

    def __init__(self, value, suite, image, position):
        super().__init__()
        self.value = value
        self.suite = suite
        self.image = image
        self.position = position
        self.rect = self.image.get_rect()
        self.selected = False
        self.dragging = False
        self.rect.center = self.position

    def select_card(self):
        self.selected = True
        if self.value == 1 or (self.value in range(1, 9) and self.suite.value == "GOLD"):
            self.image = pygame.image.load(f"assets/c{self.value}_{self.suite.value}_SCALED_SELECTED.png")
        else:
            self.image = pygame.image.load("assets/scaled_negativo.png")
        self.rect.y -= 30

    def unselect_card(self):
        self.selected = False
        if self.value == 1 or (self.value in range(1, 9) and self.suite.value == "GOLD"):
            self.image = pygame.image.load(f"assets/c{self.value}_{self.suite.value}_SCALED.png")
        else:
            self.image = pygame.image.load(f"assets/c{self.value}_{self.suite.value}.png")
        self.rect.y += 30

    def drag_card(self):
        self.dragging = True

    def undrag_card(self):
        self.dragging = False
        self.rect.center = self.position

    def is_dragging(self):
        return self.dragging
