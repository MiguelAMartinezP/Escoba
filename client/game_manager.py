from models import Player, Bot, Deck, GameController, CardModel
from kivy.app import App
from typing import List, Optional


class GameManager:
    """Manages the game state and integrates with the UI."""
    def __init__(self):
        self.controller: Optional[GameController] = None
        self.human_player: Optional[Player] = None
        self.bot_player: Optional[Bot] = None

    def start_new_game(self, human_name: str = "Player", difficulty: str = "medium"):
        """Start a new game with human and bot."""
        print(f"[GameManager] Creating new game - Player: {human_name}, Difficulty: {difficulty}")
        self.human_player = Player(human_name)
        self.bot_player = Bot(difficulty=difficulty)
        print(f"[GameManager] Bot created with difficulty: {self.bot_player.difficulty}")
        self.controller = GameController([self.human_player, self.bot_player])
        self.controller.start_game()
        print(f"[GameManager] Game started")

    def play_human_turn(self, card: CardModel, selected_table_cards: Optional[List[str]] = None) -> bool:
        """Play a turn for the human player."""
        if not self.controller or self.controller.current_player != self.human_player:
            return False
        # Find the selected table cards
        selected = []
        if selected_table_cards:
            try:
                app = App.get_running_app()
                debug = getattr(app, 'debug_mode', False)
            except Exception:
                debug = False
            if debug:
                print(f"[DEBUG] UI selected strings: {selected_table_cards}")
                print(f"[DEBUG] Table cards available: {[str(c) for c in self.controller.table_cards]}")
            for table_card in self.controller.table_cards:
                card_str = str(table_card)
                if debug:
                    print(f"[DEBUG] Checking if '{card_str}' in {selected_table_cards}")
                if card_str in selected_table_cards:
                    if debug:
                        print(f"[DEBUG] MATCH FOUND: {card_str} -> {table_card} (rank={table_card.rank})")
                    selected.append(table_card)
        return self.controller.play_turn(self.human_player, card, selected)

    def play_bot_turn(self):
        """Play a turn for the bot."""
        if not self.controller or self.controller.current_player != self.bot_player:
            return
        card, selected_cards = self.bot_player.choose_card_to_play(self.controller.table_cards)
        if card:
            self.controller.play_turn(self.bot_player, card, selected_cards)

    def get_game_state(self) -> dict:
        """Get the current game state for UI updates."""
        if not self.controller:
            return {}
        
        # Debug: Check for duplicates in hand
        hand_strs = [str(card) for card in self.human_player.hand]
        hand_set = set(hand_strs)
        if len(hand_strs) != len(hand_set):
            print(f"[WARNING] Duplicates detected in human hand!")
            print(f"  Hand list: {hand_strs}")
            print(f"  Unique: {list(hand_set)}")
            # Show which cards are duplicated
            from collections import Counter
            counts = Counter(hand_strs)
            for card_str, count in counts.items():
                if count > 1:
                    print(f"    {card_str} appears {count} times")
        
        return {
            'current_player': self.controller.current_player.name,
            'human_hand': hand_strs,
            'bot_hand': [str(card) for card in self.bot_player.hand],
            'table_cards': [str(card) for card in self.controller.table_cards],
            'game_over': self.controller.is_game_over(),
            'deck_cards_left': len(self.controller.deck.cards)
        }

    def check_game_end(self):
        """Check if game is over and handle end game."""
        if self.controller and self.controller.is_game_over():
            self.controller.end_game()
            winner = self.controller.get_winner()
            return winner.name if winner else "Tie"
        return None
