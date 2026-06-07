from kivy.factory import Factory
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty
from kivy.app import App
from game_manager import GameManager
from multiplayer import MultiplayerClient
from language_manager import get_language_manager
import json
import socket


class MenuScreen(Screen):
    btn_play = StringProperty("Jugar")
    btn_tutorial = StringProperty("Tutorial")
    btn_exit = StringProperty("Salir")
    btn_language = StringProperty("Idioma")
    confirm_exit_text = StringProperty("¿Seguro que quieres salir?")
    btn_yes = StringProperty("Sí")
    btn_no = StringProperty("No")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()
    
    def update_language_text(self, *args):
        """Update all menu text based on current language."""
        self.btn_play = self.language_manager.translate("menu.play")
        self.btn_tutorial = self.language_manager.translate("menu.tutorial")
        self.btn_exit = self.language_manager.translate("menu.exit")
        self.btn_language = self.language_manager.translate("menu.language")
        self.confirm_exit_text = self.language_manager.translate("dialogs.confirm_exit")
        self.btn_yes = self.language_manager.translate("dialogs.yes")
        self.btn_no = self.language_manager.translate("dialogs.no")
    
    def change_language(self):
        """Cycle through available languages."""
        languages = self.language_manager.get_available_languages()
        current_idx = languages.index(self.language_manager.current_language)
        next_idx = (current_idx + 1) % len(languages)
        self.language_manager.set_language(languages[next_idx])


class GameScreen(Screen):
    current_player = StringProperty("Human")
    deck_cards_left = StringProperty("")
    human_turn = BooleanProperty(True)
    deck_cards_label = StringProperty("")
    turn_label = StringProperty("")
    exit_button = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_manager = GameManager()
        self.popup_opened = False
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()
        
        # Multiplayer support
        self.multiplayer_mode = False
        self.is_host = False
        self.opponent_name = ""
        self.multiplayer_client = None
        self._original_on_message = None
        self._original_on_status = None
        self._original_on_error = None
        self._game_status_handler = None
        self._game_error_handler = None

    def update_language_text(self, *args):
        self.deck_cards_label = self.language_manager.translate("game.cards_left")
        self.turn_label = self.language_manager.translate("game.turn")
        self.exit_button = self.language_manager.translate("game.exit")

    def show_error_message(self, message: str, duration: float = 2.0):
        """Show an error message that disappears after the specified duration."""
        self.ids.error_message.text = message
        self.ids.error_message.opacity = 1
        
        def hide_message(dt):
            self.ids.error_message.opacity = 0
            self.ids.error_message.text = ""
        
        Clock.schedule_once(hide_message, duration)

    def on_enter(self):
        # Check if we're coming from multiplayer lobby
        try:
            app = App.get_running_app()
            lobby_screen = app.root.get_screen("lobby")
            if lobby_screen.opponent_ready or (not lobby_screen.is_host and lobby_screen.host_name_received):
                # Initialize multiplayer game
                self.multiplayer_mode = True
                self.is_host = lobby_screen.is_host
                self.opponent_name = lobby_screen.opponent_name
                self.player_name = lobby_screen.current_player_name
                self.multiplayer_client = lobby_screen.client
                
                # Subscribe game-specific message handlers
                self.multiplayer_client.add_message_handler(self._on_multiplayer_message)
                self._game_status_handler = lambda msg: print(f"[GAME STATUS] {msg}")
                self._game_error_handler = lambda msg: print(f"[GAME ERROR] {msg}")
                self.multiplayer_client.add_status_handler(self._game_status_handler)
                self.multiplayer_client.add_error_handler(self._game_error_handler)
                
                print(f"[GAME] Message handlers subscribed for game screen")
                
                # Initialize multiplayer game
                self._init_multiplayer_game()
                
                # Check if game_init was already received while in lobby
                if lobby_screen.game_init_data and not self.is_host:
                    print(f"[GAME] Found stored game_init data from lobby, processing it now")
                    self._setup_game_from_opponent(lobby_screen.game_init_data)
                    # Send confirmation
                    self.multiplayer_client.send_game_message({
                        "type": "game_ready",
                        "player_name": self.game_manager.human_player.name
                    })
                    print(f"[GAME] Processed stored game_init and sent game_ready")
                    lobby_screen.game_init_data = None  # Clear it so we don't process it again
                
                return
        except Exception as e:
            print(f"[ERROR] Failed to detect multiplayer: {e}")
        
        # Solo game
        self.multiplayer_mode = False
        # Only initialize if not already initialized (to preserve difficulty from GameConfigScreen)
        if not self.game_manager.bot_player:
            print(f"[GAME] on_enter: Initializing new solo game with default difficulty")
            self.game_manager.start_new_game("Player")
        else:
            print(f"[GAME] on_enter: Game already initialized with difficulty: {self.game_manager.bot_player.difficulty}")
        self.popup_opened = False
        self.update_ui()

    def _init_multiplayer_game(self):
        """Initialize a multiplayer game with both player names."""
        from models import Player, GameController
        
        user_name = getattr(self, 'player_name', None) or "Player"
        opponent_name = self.opponent_name or "Opponent"
        
        player1 = Player(user_name, is_human=True)
        player2 = Player(opponent_name, is_human=False)  # Remote player
        
        self.game_manager.human_player = player1
        self.game_manager.bot_player = player2
        
        controller = GameController([player1, player2])
        self.game_manager.controller = controller
        
        if self.is_host:
            # Host initializes and starts the game
            controller.start_game()
            self._send_game_state_to_opponent()
            print(f"[GAME] Host initialized multiplayer game")
            self.update_ui()
        else:
            # Wait for host to send initial game state
            print(f"[GAME] Joined player waiting for game state from host")
        
        self.popup_opened = False

    def _send_game_state_to_opponent(self):
        """Send the current game state to the opponent."""
        if not self.multiplayer_client or not self.multiplayer_client.connected:
            print(f"[ERROR] Cannot send game state: not connected")
            return
        
        state = self.game_manager.get_game_state()
        self.multiplayer_client.send_game_message({
            "type": "game_init",
            "player1_name": self.game_manager.human_player.name,
            "player1_hand": state['human_hand'],
            "player2_name": self.opponent_name,
            "player2_hand": state['bot_hand'],
            "table_cards": state['table_cards'],
            "current_player_index": self.game_manager.controller.current_player_index,
            "deck_cards": [str(card) for card in self.game_manager.controller.deck.cards]
        })
        print(f"[GAME] Sent game state to opponent")

    def _on_multiplayer_message(self, message: str):
        """Handle messages from multiplayer opponent."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            print(f"[GAME MESSAGE] Type: {msg_type}, Data keys: {list(data.keys())}")
            
            if msg_type == "game_init":
                # Joined player receives initial game state
                print(f"[GAME] Received game_init, is_host={self.is_host}")
                if not self.is_host:
                    print(f"[GAME] Setting up game from opponent data...")
                    # Schedule on main thread (this handler runs on websocket thread)
                    def setup_game(dt):
                        try:
                            self._setup_game_from_opponent(data)
                            print(f"[GAME] Game setup complete, sending confirmation...")
                            # Send confirmation back
                            self.multiplayer_client.send_game_message({
                                "type": "game_ready",
                                "player_name": self.game_manager.human_player.name
                            })
                            print(f"[GAME] Sent game_ready confirmation to host")
                        except Exception as e:
                            print(f"[ERROR] Failed to setup game from opponent: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    Clock.schedule_once(setup_game, 0)
            elif msg_type == "game_ready":
                # Host receives confirmation that opponent is ready
                print(f"[GAME] Opponent confirmed game ready")
            elif msg_type == "play_turn":
                # Opponent played a card
                print(f"[GAME] Received opponent play_turn message")
                if self.multiplayer_client:
                    # Schedule on main thread
                    def handle_play(dt):
                        self._handle_opponent_play(data)
                    Clock.schedule_once(handle_play, 0)
            elif msg_type == "draw_cards":
                # New hand from opponent
                print(f"[GAME] Received draw_cards message")
                if self.multiplayer_client:
                    # Schedule on main thread
                    def handle_draw(dt):
                        self._handle_draw_cards(data)
                    Clock.schedule_once(handle_draw, 0)
            elif msg_type == "game_over":
                # Game finished
                print(f"[GAME] Received game_over message")
                # Schedule on main thread
                def handle_over(dt):
                    self._handle_game_over(data)
                Clock.schedule_once(handle_over, 0)
            else:
                print(f"[GAME] Unknown message type: {msg_type}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse game message: {e}")
        except Exception as e:
            print(f"[ERROR] Exception in _on_multiplayer_message: {e}")
            import traceback
            traceback.print_exc()

    def _setup_game_from_opponent(self, game_data):
        """Setup the game from data received from opponent."""
        from models import Player, CardModel, GameController
        
        print(f"[GAME] Starting game setup from opponent data...")
        p1_name = game_data.get("player1_name", "Host")
        p2_name = game_data.get("player2_name", "Opponent")
        p1_hand_strs = game_data.get("player1_hand", [])
        p2_hand_strs = game_data.get("player2_hand", [])
        table_strs = game_data.get("table_cards", [])
        deck_strs = game_data.get("deck_cards", [])
        current_player_index = game_data.get("current_player_index", 0)
        
        print(f"[GAME] P1: {p1_name} with {len(p1_hand_strs)} cards")
        print(f"[GAME] P2: {p2_name} with {len(p2_hand_strs)} cards")
        print(f"[GAME] Table: {len(table_strs)} cards, Deck: {len(deck_strs)} cards")
        
        # Create players
        player1 = Player(p1_name, is_human=False)
        player2 = Player(p2_name, is_human=True)  # This client is player 2
        
        self.player_name = p2_name
        self.game_manager.human_player = player2
        self.game_manager.bot_player = player1
        
        controller = GameController([player1, player2])
        self.game_manager.controller = controller
        
        # Set deck order from host before dealing cards
        print(f"[GAME] Setting deck with {len(deck_strs)} cards...")
        controller.deck.cards = []
        for card_str in deck_strs:
            card = self._parse_card_string(card_str)
            if card:
                controller.deck.cards.append(card)
        print(f"[GAME] Deck now has {len(controller.deck.cards)} cards")
        
        # Set up hands explicitly
        print(f"[GAME] Setting up player hands...")
        player1.hand = []
        player2.hand = []
        
        for card_str in p1_hand_strs:
            card = self._parse_card_string(card_str)
            if card:
                player1.add_card_to_hand(card)
                print(f"[GAME] Added {card} to {p1_name}")
        
        for card_str in p2_hand_strs:
            card = self._parse_card_string(card_str)
            if card:
                player2.add_card_to_hand(card)
                print(f"[GAME] Added {card} to {p2_name}")
        
        # Set up table explicitly
        print(f"[GAME] Setting up table cards...")
        controller.table_cards = []
        for card_str in table_strs:
            card = self._parse_card_string(card_str)
            if card:
                controller.table_cards.append(card)
                print(f"[GAME] Added {card} to table")
        
        controller.current_player_index = current_player_index
        
        print(f"[GAME] Game setup complete:")
        print(f"[GAME]   {p1_name} hand: {[str(c) for c in player1.hand]}")
        print(f"[GAME]   {p2_name} hand: {[str(c) for c in player2.hand]}")
        print(f"[GAME]   Table: {[str(c) for c in controller.table_cards]}")
        print(f"[GAME]   Current player index: {current_player_index}")
        
        self.update_ui()
        print(f"[GAME] UI updated, game is ready to play")

    def _parse_card_string(self, card_str: str):
        """Parse a card string like '7 de oros' to CardModel."""
        from models import CardModel
        try:
            parts = card_str.split(" de ")
            if len(parts) == 2:
                rank = int(parts[0])
                suit = parts[1]
                return CardModel(suit, rank)
        except:
            pass
        return None

    def _handle_opponent_play(self, play_data):
        """Handle opponent's move with visual feedback."""
        card_str = play_data.get("card")
        selected_strs = play_data.get("selected_cards", [])
        
        if not card_str:
            print(f"[ERROR] No card in opponent play data")
            return
        
        print(f"[OPPONENT] Received play: {card_str}, capturing: {selected_strs}")
        
        # Find card in opponent's hand (bot_player)
        card = self._parse_card_string(card_str)
        if not card:
            print(f"[ERROR] Could not parse card: {card_str}")
            return
        
        if card not in self.game_manager.bot_player.hand:
            print(f"[ERROR] Card {card_str} not in opponent hand: {[str(c) for c in self.game_manager.bot_player.hand]}")
            return
        
        # Find selected table cards
        selected = []
        for sel_str in selected_strs:
            sel_card = self._parse_card_string(sel_str)
            if sel_card and sel_card in self.game_manager.controller.table_cards:
                selected.append(sel_card)
            else:
                print(f"[WARNING] Selected card {sel_str} not found on table: {[str(c) for c in self.game_manager.controller.table_cards]}")
        
        # Show opponent's move visually for 2 seconds, then execute
        print(f"[OPPONENT] Playing: {card_str}")
        print(f"[OPPONENT] Capturing: {selected_strs}")
        
        # Schedule highlight on main thread (websocket runs on different thread)
        def show_highlight(dt):
            print(f"[OPPONENT] Showing highlight on main thread")
            try:
                self.ids.card_game.highlight_bot_move(card_str, selected_strs)
                print(f"[OPPONENT] Highlight applied")
            except Exception as e:
                print(f"[ERROR] Failed to highlight: {e}")
        
        Clock.schedule_once(show_highlight, 0)
        
        # Execute the move after visual display
        def continue_opponent_turn(dt):
            print(f"[OPPONENT] Executing play after visual display")
            try:
                # Clear highlights
                self.ids.card_game.clear_bot_highlights()
                # Execute the opponent's turn
                self.game_manager.controller.play_turn(self.game_manager.bot_player, card, selected)
                print(f"[OPPONENT] Move executed, current player is now: {self.game_manager.controller.current_player.name}")
                self.update_ui()
                print(f"[OPPONENT] UI updated, human_turn is now: {self.human_turn}")
            except Exception as e:
                print(f"[ERROR] Failed to execute opponent play: {e}")
                import traceback
                traceback.print_exc()
        
        Clock.schedule_once(continue_opponent_turn, 2.0)  # 2 second delay to show the move

    def _handle_draw_cards(self, draw_data):
        """Handle receiving new cards from opponent."""
        hand_strs = draw_data.get("hand", [])
        
        # Schedule UI update on main thread
        def update_hand(dt):
            # Clear current hand and add new cards
            self.game_manager.human_player.hand = []
            for card_str in hand_strs:
                card = self._parse_card_string(card_str)
                if card:
                    self.game_manager.human_player.add_card_to_hand(card)
            
            self.update_ui()
            print(f"[OPPONENT] Draw cards handled")
        
        Clock.schedule_once(update_hand, 0)

    def _handle_game_over(self, game_data):
        """Handle game over message."""
        # Schedule on main thread
        def on_game_over(dt):
            self.popup_opened = True
            print(f"[GAME] Game Over message received")
        
        Clock.schedule_once(on_game_over, 0)

    def update_ui(self):
        state = self.game_manager.get_game_state()
        self.current_player = state['current_player']
        self.deck_cards_left = str(state['deck_cards_left'])
        if self.multiplayer_mode:
            local_name = getattr(self, 'player_name', None) or (self.game_manager.human_player.name if self.game_manager.human_player else "Player")
            self.human_turn = state['current_player'] == local_name
        else:
            self.human_turn = state['current_player'] != "Bot"
        # Update the card game UI
        self.ids.card_game.update_hands(state['human_hand'], state['bot_hand'], self.human_turn)
        self.ids.card_game.update_table(state['table_cards'])

        if state.get('game_over') and not self.popup_opened:
            self.popup_opened = True
            players = self.game_manager.controller.get_players()
            winner = None
            if players:
                if all(p.score["total"] == players[0].score["total"] for p in players):
                    winner_text = "Empate"
                else:
                    winner = max(players, key=lambda p: p.score["total"])
                    loser = min(players, key=lambda p: p.score["total"])
                    winner_text = winner.name
            popup = Factory.WinnerPopup()
            if winner:
                message_text = (
                    f"Total: {winner.name}: {winner.score['total']} - {loser.name}: {loser.score['total']}\n"
                    f"Ganador: {winner_text}\n\n"
                    f"Cartas: {winner.name if winner.score['cards'] else loser.name if loser.score['cards'] else 'Empate'}\n"
                    f"Oros: {winner.name if winner.score['golds'] else loser.name if loser.score['golds'] else 'Empate'}\n"
                    f"Sietes: {winner.name if winner.score['sevens'] else loser.name if loser.score['sevens'] else 'Empate'}\n"
                    f"Siete de oros: {winner.name if winner.score['golden_seven'] else loser.name if loser.score['golden_seven'] else 'Empate'}\n"
                    f"Escobas: {winner.name}: {winner.score['escobas']} - {loser.name}: {loser.score['escobas']}\n"
                )
            else:
                # TODO dejar el ganador de cada categoria (cartas, oros ...) en una variable, independiente de winner o loser
                message_text = f"{winner_text}"
            popup.ids.message.text = message_text
            popup.open()

    def restart_game(self):
        self.popup_opened = False
        self.game_manager.start_new_game("Player")
        self.update_ui()

    def on_leave(self):
        """Clean up when leaving the game screen."""
        try:
            if self.multiplayer_client:
                print(f"[GAME] Leaving game screen, unsubscribing handlers")
                self.multiplayer_client.remove_message_handler(self._on_multiplayer_message)
                if self._game_status_handler:
                    self.multiplayer_client.remove_status_handler(self._game_status_handler)
                    self._game_status_handler = None
                if self._game_error_handler:
                    self.multiplayer_client.remove_error_handler(self._game_error_handler)
                    self._game_error_handler = None
            
            app = App.get_running_app()
            lobby_screen = app.root.get_screen("lobby")
            # Clear stored game_init_data to prevent reuse
            lobby_screen.game_init_data = None
        except Exception as e:
            print(f"[ERROR] Exception in GameScreen.on_leave: {e}")

    def play_bot_turn_with_feedback(self):
        """Play bot turn with visual feedback showing what the bot is doing."""
        if not self.game_manager.controller or self.game_manager.controller.current_player != self.game_manager.bot_player:
            return
        
        # Get bot's move
        card, selected_cards = self.game_manager.bot_player.choose_card_to_play(self.game_manager.controller.table_cards)
        if card:
            # Show bot's move visually
            played_card_str = str(card)
            captured_card_strs = [str(c) for c in selected_cards]
            
            print(f"[BOT] Playing: {played_card_str}")
            print(f"[BOT] Capturing: {captured_card_strs}")
            
            # Highlight the bot's move
            self.ids.card_game.highlight_bot_move(played_card_str, captured_card_strs)
            
            # For now, automatically continue after a short delay
            # In a real game, you might want to wait for user input
            from kivy.clock import Clock
            def continue_bot_turn(dt):
                # Clear highlights
                self.ids.card_game.clear_bot_highlights()
                # Execute the bot's turn
                self.game_manager.controller.play_turn(self.game_manager.bot_player, card, selected_cards)
                self.update_ui()
            
            Clock.schedule_once(continue_bot_turn, 2.0)  # 2 second delay

    def play_card(self, card_str):
        # Find the CardModel from string
        print(f"\n[PLAY] Clicked card string: '{card_str}'")
        print(f"[PLAY] Cards in hand: {[str(c) for c in self.game_manager.human_player.hand]}")
        
        # Check if it's the human player's turn
        if not self.human_turn:
            print(f"[PLAY] Not human's turn - current player: {self.game_manager.controller.current_player.name}")
            self.show_error_message("No es tu turno")
            return False
        
        found = False
        for i, card in enumerate(self.game_manager.human_player.hand):
            card_display = str(card)
            print(f"[PLAY] Checking hand[{i}]: '{card_display}' == '{card_str}' ? {card_display == card_str}")
            if card_display == card_str:
                found = True
                print(f"[PLAY] MATCH! Playing {card}")
                
                # Get selected table cards
                selected = self.ids.card_game.get_selected_table_cards()
                
                # Validate that the combination sums to 15 (only if cards are selected)
                if selected and not self._validate_play(card, selected):
                    self.show_error_message("La combinación debe sumar 15")
                    # Clear selections and let player try again
                    self.ids.card_game.clear_selections()
                    return False  # Play was invalid
                
                success = self.game_manager.play_human_turn(card, selected)
                if success:
                    print(f"[PLAY] Human play successful")
                    self.update_ui()
                    
                    # In multiplayer, send the move to opponent
                    if self.multiplayer_mode and self.multiplayer_client:
                        self.multiplayer_client.send_game_message({
                            "type": "play_turn",
                            "card": card_str,
                            "selected_cards": selected
                        })
                        print(f"[PLAY] Sent play move to opponent, waiting for their response...")
                    elif not self.multiplayer_mode:
                        # Solo game: If bot's turn, play bot with visual feedback
                        if self.game_manager.controller.current_player == self.game_manager.bot_player:
                            self.play_bot_turn_with_feedback()
                    
                    return True  # Play was successful
                else:
                    print(f"[PLAY] Human play failed - invalid move")
                break
        
        if not found:
            print(f"[PLAY] NO MATCH FOUND for '{card_str}'")
        
        return False  # Card not found or play failed

    def _validate_play(self, played_card, selected_table_card_strs):
        """Validate that the played card + selected table cards sum to 15."""
        if not selected_table_card_strs:
            # No cards selected - always valid (just place card on table)
            return True
        
        # Convert selected card strings to CardModel objects
        selected_cards = []
        for card_str in selected_table_card_strs:
            for table_card in self.game_manager.controller.table_cards:
                if str(table_card) == card_str:
                    selected_cards.append(table_card)
                    break
        
        # Check if selected cards + played card sum to 15
        played_value = played_card.value()
        selected_values = [card.value() for card in selected_cards]
        total = played_value + sum(selected_values)
        return total == 15



class ConstructionScreen(Screen):
    pass


class PlayScreen(Screen):
    title_text = StringProperty("")
    solo_button = StringProperty("")
    multiplayer_button = StringProperty("")
    back_button = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()

    def update_language_text(self, *args):
        self.title_text = self.language_manager.translate("play.title")
        self.solo_button = self.language_manager.translate("play.solo")
        self.multiplayer_button = self.language_manager.translate("play.multiplayer")
        self.back_button = self.language_manager.translate("play.back")


class GameConfigScreen(Screen):
    title_text = StringProperty("")
    difficulty_text = StringProperty("")
    easy_button = StringProperty("")
    medium_button = StringProperty("")
    hard_button = StringProperty("")
    back_button = StringProperty("")
    selected_difficulty = StringProperty("medium")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()

    def update_language_text(self, *args):
        self.title_text = self.language_manager.translate("game_config.title")
        self.difficulty_text = self.language_manager.translate("game_config.select_difficulty")
        self.easy_button = self.language_manager.translate("game_config.easy")
        self.medium_button = self.language_manager.translate("game_config.medium")
        self.hard_button = self.language_manager.translate("game_config.hard")
        self.back_button = self.language_manager.translate("game_config.back")

    def start_game(self, difficulty: str):
        """Start a new solo game with the selected difficulty."""
        print(f"[GAME_CONFIG] Starting game with difficulty: {difficulty}")
        app = App.get_running_app()
        app.root.current = "game"
        
        # Get the game screen and start a new game with the selected difficulty
        game_screen = app.root.get_screen("game")
        print(f"[GAME_CONFIG] Game screen obtained, initializing with difficulty: {difficulty}")
        game_screen.game_manager.start_new_game("Player", difficulty=difficulty)
        print(f"[GAME_CONFIG] Bot difficulty set to: {game_screen.game_manager.bot_player.difficulty}")
        game_screen.multiplayer_mode = False
        game_screen.popup_opened = False
        game_screen.update_ui()
        print(f"[GAME_CONFIG] Game initialized and UI updated")


class MultiplayerConfigScreen(Screen):
    server_status = StringProperty("")
    connection_error = BooleanProperty(False)  # True if there's a connection error
    title_text = StringProperty("")
    player_label = StringProperty("")
    room_label = StringProperty("")
    create_button = StringProperty("")
    join_button = StringProperty("")
    back_button = StringProperty("")
    invalid_player_message = StringProperty("")
    invalid_room_message = StringProperty("")
    creating_lobby_message = StringProperty("")
    joining_lobby_message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = MultiplayerClient(
            on_status=self._on_status,
            on_message=self._on_message,
            on_error=self._on_error,
        )
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()

    def on_enter(self):
        self._update_initial_server_status()

    def _check_server_reachable(self) -> bool:
        try:
            sock = socket.create_connection(("localhost", 8080), timeout=0.5)
            sock.close()
            return True
        except OSError:
            return False

    def _update_initial_server_status(self):
        if self._check_server_reachable():
            self.server_status = self.language_manager.translate("multiplayer.status_ready")
            self.connection_error = False
        else:
            self.server_status = self.language_manager.translate("multiplayer.status_cannot_connect")
            self.connection_error = True

    def update_language_text(self, *args):
        self.title_text = self.language_manager.translate("multiplayer.title")
        self.player_label = self.language_manager.translate("multiplayer.player_name")
        self.room_label = self.language_manager.translate("multiplayer.room_name")
        self.create_button = self.language_manager.translate("multiplayer.create_lobby")
        self.join_button = self.language_manager.translate("multiplayer.join_lobby")
        self.back_button = self.language_manager.translate("multiplayer.back")
        self.invalid_player_message = self.language_manager.translate("multiplayer.error_invalid_player")
        self.invalid_room_message = self.language_manager.translate("multiplayer.error_invalid_room")
        self.creating_lobby_message = self.language_manager.translate("multiplayer.status_creating")
        self.joining_lobby_message = self.language_manager.translate("multiplayer.status_joining")
        self.server_status = self.language_manager.translate("multiplayer.status_ready")

    def create_lobby(self):
        player_name = self.ids.player_input.text.strip()
        if not player_name:
            self.server_status = self.invalid_player_message
            return
        room = self.ids.lobby_input.text.strip()
        if not room:
            self.server_status = self.invalid_room_message
            return
        self.server_status = self.creating_lobby_message
        self.connection_error = False
        self.client.connect(create=True, room=room, player_name=player_name)

    def join_lobby(self):
        player_name = self.ids.player_input.text.strip()
        if not player_name:
            self.server_status = self.invalid_player_message
            return
        room = self.ids.lobby_input.text.strip()
        if not room:
            self.server_status = self.invalid_room_message
            return
        self.server_status = self.joining_lobby_message
        self.connection_error = False
        self.client.connect(create=False, room=room, player_name=player_name)

    def disconnect(self):
        self.client.disconnect()

    def _on_status(self, message: str):
        def update_status(dt):
            self.server_status = message
            self.connection_error = False  # Clear error flag on status update
        Clock.schedule_once(update_status, 0)

    def _on_message(self, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            # Ignore game messages here; they are handled by lobby/game screens.
            if msg_type in ["game_init", "game_ready", "play_turn", "draw_cards", "game_over"]:
                return
            if msg_type in ["lobby_created", "lobby_joined"]:
                Clock.schedule_once(self._go_to_lobby)
        except json.JSONDecodeError:
            pass

    def _on_error(self, message: str):
        def update_error(dt):
            self.server_status = message
            self.connection_error = True  # Set error flag when error occurs
        Clock.schedule_once(update_error, 0)

    def _go_to_lobby(self, dt=None):
        app = App.get_running_app()
        app.root.current = "lobby"


class LobbyScreen(Screen):
    current_player_name = StringProperty("")
    opponent_name = StringProperty("")
    room_id = StringProperty("")
    is_host = BooleanProperty(False)
    opponent_ready = BooleanProperty(False)
    player_ready = BooleanProperty(False)
    host_name_received = BooleanProperty(False)  # Track if joined player received host name
    title_text = StringProperty("")
    room_label_prefix = StringProperty("")
    player_label_prefix = StringProperty("")
    opponent_label_prefix = StringProperty("")
    waiting_text = StringProperty("")
    leave_button = StringProperty("")
    create_game_button = StringProperty("")
    ready_button_text = StringProperty("")
    opponent_ready_message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.language_manager = get_language_manager()
        self.language_manager.bind(on_language_changed=self.update_language_text)
        self.update_language_text()
        # Store original callbacks
        self._original_on_message = None
        self._original_on_status = None
        self._original_on_error = None
        self._lobby_message_handler = None
        self._lobby_status_handler = None
        self._lobby_error_handler = None
        # Store game_init data for the game screen
        self.game_init_data = None

    def update_language_text(self, *args):
        self.title_text = self.language_manager.translate("lobby.title")
        self.room_label_prefix = self.language_manager.translate("lobby.room")
        self.player_label_prefix = self.language_manager.translate("lobby.player")
        self.opponent_label_prefix = self.language_manager.translate("lobby.opponent")
        self.waiting_text = self.language_manager.translate("lobby.waiting")
        self.leave_button = self.language_manager.translate("lobby.leave")
        self.create_game_button = self.language_manager.translate("lobby.create_game")
        self.ready_button_text = self.language_manager.translate("lobby.ready_to_play")
        self.opponent_ready_message = self.language_manager.translate("lobby.opponent_ready")

    def on_enter(self):
        try:
            # Get the client from the previous screen (multiplayer_config)
            app = App.get_running_app()
            config_screen = app.root.get_screen("multiplayer_config")
            self.client = config_screen.client
            
            # Store original callbacks instead of replacing them (only if not already stored)
            if self._original_on_message is None:
                self._original_on_message = self.client.on_message
            if self._original_on_status is None:
                self._original_on_status = self.client.on_status
            if self._original_on_error is None:
                self._original_on_error = self.client.on_error
            
            # Subscribe lobby-specific handlers without replacing the existing config handlers
            self._lobby_message_handler = self._on_message
            self._lobby_status_handler = self._on_status
            self._lobby_error_handler = self._on_error
            self.client.add_message_handler(self._lobby_message_handler)
            self.client.add_status_handler(self._lobby_status_handler)
            self.client.add_error_handler(self._lobby_error_handler)
            
            # Get player name and room info from config screen
            self.current_player_name = config_screen.ids.player_input.text.strip()
            self.room_id = config_screen.ids.lobby_input.text.strip()
            self.is_host = config_screen.client._create_room
            
            print(f"[LOBBY] Entered lobby - Player: {self.current_player_name}, Room: {self.room_id}, Host: {self.is_host}")
            
            # If this player is not the host, announce their name to the host
            if not self.is_host:
                self.client.send_game_message({
                    "type": "player_announce",
                    "player_name": self.current_player_name
                })
                print(f"[LOBBY] Sent name announcement to host")
        except Exception as e:
            print(f"[ERROR] LobbyScreen.on_enter() failed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_leave(self):
        """Restore original callbacks when leaving the lobby screen."""
        try:
            if self.client:
                if self._lobby_message_handler:
                    self.client.remove_message_handler(self._lobby_message_handler)
                    self._lobby_message_handler = None
                if self._lobby_status_handler:
                    self.client.remove_status_handler(self._lobby_status_handler)
                    self._lobby_status_handler = None
                if self._lobby_error_handler:
                    self.client.remove_error_handler(self._lobby_error_handler)
                    self._lobby_error_handler = None
                print("[LOBBY] Left lobby - handlers unsubscribed")
            # Reset ready states
            self.opponent_ready = False
            self.player_ready = False
            self.host_name_received = False
            self.opponent_name = ""
        except Exception as e:
            print(f"[ERROR] LobbyScreen.on_leave() failed: {e}")
            import traceback
            traceback.print_exc()
        
    def leave_lobby(self):
        if self.client:
            self.client.disconnect()
        # Return to multiplayer config screen
        app = App.get_running_app()
        app.root.current = "multiplayer_config"
        
    def ready_to_play(self):
        """Joined player indicates they are ready to play."""
        if self.client and self.client.connected and self.host_name_received:
            self.player_ready = True
            self.client.send_game_message({
                "type": "player_ready",
                "player_name": self.current_player_name
            })
            print(f"[LOBBY] Sent ready status to host")

    def create_game(self):
        # Host sends message to start the game when opponent is ready
        if self.client and self.client.connected and self.opponent_ready and self.is_host:
            # Notify server/opponent (optional, server may forward)
            try:
                self.client.send_game_message({
                    "type": "start_game",
                    "player_name": self.current_player_name
                })
            except Exception:
                pass
            print(f"[LOBBY] Host creating game")
            # Transition to game screen so host initializes the game locally
            app = App.get_running_app()
            app.root.current = "game"
            return
        # If not host or not ready, do nothing
        
    def _on_message(self, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            print(f"[LOBBY MESSAGE] Type: {msg_type}, Data: {data}")
            
            if msg_type == "player_announce":
                # Host receives the joined player's announcement
                if self.is_host:
                    opponent_name = data.get("player_name", "Opponent")
                    print(f"[LOBBY] Received player announcement: {opponent_name}")
                    Clock.schedule_once(lambda dt: setattr(self, "opponent_name", opponent_name))
                    # Host responds with their name
                    self.client.send_game_message({
                        "type": "host_announce",
                        "player_name": self.current_player_name
                    })
                    print(f"[LOBBY] Sent host announcement")
            elif msg_type == "host_announce":
                # Joined player receives the host's name
                if not self.is_host:
                    host_name = data.get("player_name", "Host")
                    print(f"[LOBBY] Received host announcement: {host_name}")
                    Clock.schedule_once(lambda dt: setattr(self, "opponent_name", host_name))
                    Clock.schedule_once(lambda dt: setattr(self, "host_name_received", True))
            elif msg_type == "player_ready":
                # Host receives ready status from joined player
                if self.is_host:
                    print(f"[LOBBY] Opponent is ready to play")
                    Clock.schedule_once(lambda dt: setattr(self, "opponent_ready", True))
            elif msg_type == "game_init":
                # Store the game initialization data for the game screen to process
                print(f"[LOBBY] Received game_init message, storing for game screen")
                self.game_init_data = data
            elif msg_type in ("start_game", "game_started"):
                if not self.is_host:
                    print(f"[LOBBY] Received start game signal")
                    Clock.schedule_once(self._start_game)
            elif msg_type == "player_left":
                print(f"[LOBBY] Player left")
                Clock.schedule_once(lambda dt: setattr(self, "opponent_name", ""))
                Clock.schedule_once(lambda dt: setattr(self, "opponent_ready", False))
                Clock.schedule_once(lambda dt: setattr(self, "host_name_received", False))
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON message: {e}")
            print(f"[ERROR] Message was: {message}")
            
    def _on_status(self, message: str):
        print(f"[LOBBY STATUS] {message}")
        
    def _on_error(self, message: str):
        print(f"[LOBBY ERROR] {message}")
        
    def _start_game(self, dt=None):
        print(f"[LOBBY] Transitioning to game screen")
        try:
            # Transition to game screen
            app = App.get_running_app()
            app.root.current = "game"
        except Exception as e:
            print(f"[ERROR] Failed to start game: {e}")
            import traceback
            traceback.print_exc()


# class CustomScreen(Screen):
#     valor_seleccionado = StringProperty("")
#     palo_seleccionado = StringProperty("")

#     def on_enter(self):
#         self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

#     def on_valor_seleccionado(self, instance, value):
#         self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

#     def on_palo_seleccionado(self, instance, value):
#         self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)


class ConfirmExitPopup(Popup):
    """Popup to confirm exit with language support."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = ""
        self.separator_height = 0
        self.size_hint = (0.5, 0.4)
        self.auto_dismiss = True
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        
        # Get language manager
        self.language_manager = get_language_manager()
        
        # Create the main layout
        main_layout = BoxLayout(orientation="vertical", spacing=20, padding=20)
        
        # Add the message label
        message_label = Label(
            text=self.language_manager.translate("dialogs.confirm_exit"),
            font_size=20
        )
        main_layout.add_widget(message_label)
        
        # Create button layout
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=20)
        
        # Yes button
        yes_btn = Button(
            text=self.language_manager.translate("dialogs.yes"),
            background_color=(0.4, 0.4, 0.4, 0.7)
        )
        yes_btn.bind(on_release=self._on_yes)
        button_layout.add_widget(yes_btn)
        
        # No button
        no_btn = Button(
            text=self.language_manager.translate("dialogs.no"),
            background_color=(0.4, 0.4, 0.4, 0.7)
        )
        no_btn.bind(on_release=self.dismiss)
        button_layout.add_widget(no_btn)
        
        main_layout.add_widget(button_layout)
        self.add_widget(main_layout)
    
    def _on_yes(self, *args):
        """Handle yes button press."""
        App.get_running_app().stop()
        self.dismiss()


# Register the custom popup with Factory
Factory.register('ConfirmExitPopup', cls=ConfirmExitPopup)