import random
from typing import List, Optional
import itertools


class CardModel:
    """Represents a playing card with suit and rank."""
    SUITS = ['oros', 'copas', 'espadas', 'bastos']  # Spanish suits
    RANKS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]  # Escoba ranks

    def __init__(self, suit: str, rank: int):
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank} de {self.suit}"

    def __eq__(self, other):
        return isinstance(other, CardModel) and self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        """Make cards hashable so we can use sets to check for duplicates."""
        return hash((self.suit, self.rank))

    def value(self) -> int:
        """Return the point value for scoring."""
        if self.rank in [10, 11, 12]:
            return self.rank - 2
        return self.rank


class Player:
    """Base player class with hand, score, and user data."""
    def __init__(self, name: str, is_human: bool = True):
        self.name = name
        self.is_human = is_human
        self.hand: List[CardModel] = []
        self.score = {"golden_seven": False, "sevens": False, "golds": False, "cards": False, "escobas": 0, "total": 0}
        self.captured_cards: List[CardModel] = []

    def add_card_to_hand(self, card: CardModel):
        """Add a card to the player's hand."""
        self.hand.append(card)

    def remove_card_from_hand(self, card: CardModel):
        """Remove a card from the player's hand."""
        if card in self.hand:
            self.hand.remove(card)

    def play_card(self, card: CardModel) -> CardModel:
        """Play a card from hand. Returns the card played."""
        self.remove_card_from_hand(card)
        return card

    def add_escoba_point(self):
        """Add an escoba point to the player's score."""
        self.score["escobas"] += 1

    def capture_cards(self, cards: List[CardModel]):
        """Add captured cards to the player's collection."""
        self.captured_cards.extend(cards)

    def get_total_points(self) -> dict:
        """Calculate total points from captured cards."""
        sevens = 0
        golds = 0

        for card in self.captured_cards:
            if card.rank == 7 and card.suit == 'oros':
                self.score["golden_seven"] = True
            if card.rank == 7:
                sevens += 1
            if card.suit == 'oros':
                golds += 1

        if sevens > 2:
            self.score["sevens"] = True
        if golds > 5:
            self.score["golds"] = True
        if len(self.captured_cards) > 20:
            self.score["cards"] = True

        self.score["total"] = sum(1 for v in self.score.values() if v is True) + self.score["escobas"]

        return self.score




class Bot(Player):
    """Bot player that inherits from Player and adds AI logic."""
    def __init__(self, name: str = "Bot"):
        super().__init__(name, is_human=False)

    def choose_card_to_play(self, table_cards: List[CardModel]) -> tuple[Optional[CardModel], List[CardModel]]:
        """Simple AI logic to choose which card to play and which cards to capture."""
        if not self.hand:
            return None, []

        # Simple strategy: try to capture if possible, else play lowest card
        for card in self.hand:
            captured_cards = self.can_capture(card, table_cards)
            if captured_cards:
                return card, captured_cards

        # If no capture possible, play the card with lowest rank
        return min(self.hand, key=lambda c: c.rank), []

    def can_capture(self, played_card: CardModel, table_cards: List[CardModel]) -> List[CardModel]:
        """Check if the played card can capture any combination on the table and return the cards to capture."""
        values = [card.value() for card in table_cards]
        played_value = played_card.value()
        
        # Check all possible combinations of table cards
        for r in range(1, len(values) + 1):
            for combo_indices in itertools.combinations(range(len(table_cards)), r):
                combo_values = [values[i] for i in combo_indices]
                if sum(combo_values) + played_value == 15:
                    # Return the actual cards, not just values
                    return [table_cards[i] for i in combo_indices]
        return []


class Deck:
    """Represents a deck of cards."""
    def __init__(self):
        self.cards: List[CardModel] = []
        self.reset()

    def reset(self):
        """Reset the deck with all cards - exactly one of each combination."""
        # Create exactly 40 unique cards (4 suits × 10 ranks)
        self.cards = [CardModel(suit, rank) for suit in CardModel.SUITS for rank in CardModel.RANKS]
        
        # Validate no duplicates
        card_set = set(self.cards)
        if len(card_set) != len(self.cards):
            raise ValueError(f"Deck has duplicates! Expected 40 unique cards, got {len(self.cards)} cards with {len(card_set)} unique")
        
        if len(self.cards) != 40:
            raise ValueError(f"Invalid deck size: {len(self.cards)}. Expected 40 cards.")
        
        # Debug: print all cards to verify uniqueness
        print(f"Deck reset: {len(self.cards)} unique cards created")
        print("Cards in deck:", sorted([str(c) for c in self.cards]))
        
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def draw_card(self) -> Optional[CardModel]:
        """Draw a card from the top of the deck."""
        if not self.cards:
            return None
        return self.cards.pop()

    def is_empty(self) -> bool:
        """Check if the deck is empty."""
        return len(self.cards) == 0


class GameController:
    """Manages the game logic, turns, and rules."""
    def __init__(self, players: List[Player]):
        self.players = players
        self.deck = Deck()
        self.table_cards: List[CardModel] = []
        self.current_player_index = 0
        self.game_over = False
        self.last_scorer: Optional[Player] = None

    @property
    def current_player(self) -> Player:
        """Get the current player."""
        return self.players[self.current_player_index]

    def start_game(self):
        """Initialize the game."""
        self.deck.reset()
        self.table_cards = []
        self.current_player_index = 0
        self.game_over = False

        # Deal initial cards
        for _ in range(3):  # Assuming 3 cards per player initially
            for player in self.players:
                card = self.deck.draw_card()
                if card:
                    player.add_card_to_hand(card)

        # Place 4 cards on table
        for _ in range(4):
            card = self.deck.draw_card()
            if card:
                self.table_cards.append(card)

    def play_turn(self, player: Player, card: CardModel, selected_table_cards: List[CardModel] = None) -> bool:
        """Play a turn for the given player with the specified card."""
        if player != self.current_player or card not in player.hand:
            return False

        played_card = player.play_card(card)
        captured = self.check_capture(played_card, selected_table_cards or [])

        if captured:
            captured.append(played_card)
            player.capture_cards(captured)
            self.table_cards = [c for c in self.table_cards if c not in captured]
            self.last_scorer = player  # Update last scorer when player captures cards
        else:
            self.table_cards.append(played_card)

        # Check if player has escoba (captured all cards on table)
        if not self.table_cards:
            player.add_escoba_point()  # Escoba point

        if player.hand.__len__() == 0 and not self.deck.is_empty():
            player.add_card_to_hand(self.deck.draw_card())
            player.add_card_to_hand(self.deck.draw_card())
            player.add_card_to_hand(self.deck.draw_card())

        if self.is_game_over():
            self.end_game()

        self.next_turn()
        return True

    def check_capture(self, played_card: CardModel, selected_table_cards: List[CardModel]) -> List[CardModel]:
        """Check if the played card captures the selected cards on the table."""
        if not selected_table_cards:
            # Auto-capture single card if possible
            played_value = played_card.value()
            target = 15
            for table_card in self.table_cards:
                if table_card.value() + played_value == target:
                    return [table_card]
            return []

        # Check if selected cards + played card sum to 15
        played_value = played_card.value()
        selected_values = [card.value() for card in selected_table_cards]
        total = played_value + sum(selected_values)
        
        # Debug output
        print(f"\n=== CAPTURE CHECK ===")
        print(f"Played: {played_card} (rank={played_card.rank}, value={played_value})")
        for sc in selected_table_cards:
            print(f"Selected: {sc} (rank={sc.rank}, value={sc.value()})")
        print(f"Total: {' + '.join(str(v) for v in [played_value] + selected_values)} = {total}")
        print(f"Match (need 15): {total == 15}")
        print(f"=== END CHECK ===\n")
        
        if total == 15:
            return selected_table_cards
        return []

    def next_turn(self):
        """Move to the next player's turn."""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.deck.is_empty() and all(len(player.hand) == 0 for player in self.players)

    def end_game(self):
        """End the game and calculate final scores."""
        self.game_over = True
        
        # Award remaining table cards to the last scorer
        if self.last_scorer and self.table_cards:
            print(f"[END_GAME] Awarding {len(self.table_cards)} remaining table cards to last scorer: {self.last_scorer.name}")
            self.last_scorer.capture_cards(self.table_cards)
            self.table_cards = []  # Clear the table
        
        # Calculate final scores based on captured cards
        for player in self.players:
            # Update the score dictionary with captured card points
            captured_score = player.get_total_points()
            player.score.update(captured_score)

    def get_players(self) -> Optional[Player]:
        """Get the players in the game."""
        return self.players
