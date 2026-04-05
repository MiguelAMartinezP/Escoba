#!/usr/bin/env python3
"""
Simple test script to demonstrate the game models.
"""
from models import Player, Bot, Deck, GameController

def main():
    # Create players
    human = Player("Human")
    bot = Bot("Bot")

    # Create game controller
    controller = GameController([human, bot])
    controller.start_game()

    print("Game started!")
    print("Human hand:", [str(c) for c in human.hand])
    print("Bot hand:", [str(c) for c in bot.hand])
    print("Table cards:", [str(c) for c in controller.table_cards])

    # Simulate a few turns
    while not controller.is_game_over() and len(human.hand) > 0:
        # Human plays first card
        card = human.hand[0]
        print("\nHuman plays:", card)
        controller.play_turn(human, card)

        print("Table after human:", [str(c) for c in controller.table_cards])
        print("Human captured:", len(human.captured_cards), "cards")

        # Bot plays
        bot_card, bot_selected = bot.choose_card_to_play(controller.table_cards)
        if bot_card:
            print("Bot plays:", bot_card, "capturing:", [str(c) for c in bot_selected])
            controller.play_turn(bot, bot_card, bot_selected)
            print("Table after bot:", [str(c) for c in controller.table_cards])
            print("Bot captured:", len(bot.captured_cards), "cards")

    controller.end_game()
    winner = controller.get_winner()
    print("\nGame over! Winner:", winner.name if winner else "Tie")
    print("Human score:", human.score)
    print("Bot score:", bot.score)

if __name__ == "__main__":
    main()