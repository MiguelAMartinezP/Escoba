from kivy.factory import Factory
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from game_manager import GameManager


class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    current_player = StringProperty("Human")
    deck_cards_left = StringProperty("")
    human_turn = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_manager = GameManager()
        self.popup_opened = False

    def show_error_message(self, message: str, duration: float = 2.0):
        """Show an error message that disappears after the specified duration."""
        self.ids.error_message.text = message
        self.ids.error_message.opacity = 1
        
        def hide_message(dt):
            self.ids.error_message.opacity = 0
            self.ids.error_message.text = ""
        
        Clock.schedule_once(hide_message, duration)

    def on_enter(self):
        self.game_manager.start_new_game("Player")
        self.popup_opened = False
        self.update_ui()

    def update_ui(self):
        state = self.game_manager.get_game_state()
        self.current_player = state['current_player']
        self.deck_cards_left = str(state['deck_cards_left'])
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
                    self.update_ui()
                    # If bot's turn, play bot with visual feedback
                    if self.game_manager.controller.current_player == self.game_manager.bot_player:
                        self.play_bot_turn_with_feedback()
                    return True  # Play was successful
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
    pass


class ConfigScreen(Screen):
    pass


class CustomScreen(Screen):
    valor_seleccionado = StringProperty("")
    palo_seleccionado = StringProperty("")

    def on_enter(self):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

    def on_valor_seleccionado(self, instance, value):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)

    def on_palo_seleccionado(self, instance, value):
        self.ids.cartagrid.mostrar_filtro(self.valor_seleccionado, self.palo_seleccionado)