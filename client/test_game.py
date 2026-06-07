"""Pytest suite for core game models and controller.

Run with:

    pytest -q
"""
import random
from typing import List

import pytest
import models

from models import CardModel, Deck, Bot, Player, GameController


def test_card_value_and_repr():
    c = CardModel('oros', 10)
    assert c.value() == 8  # 10 -> 8
    assert 'oros' in repr(c)


def test_deck_unique_and_size():
    d = Deck()
    # After reset in constructor, deck should have 40 unique cards
    assert len(d.cards) == 40
    assert len(set(d.cards)) == 40





def _make_table():
    # 1 of cups, 3 of swords, 5 of cups, 3 of clubs, 2 of swords
    return [
        CardModel('copas', 1),
        CardModel('espadas', 3),
        CardModel('copas', 5),
        CardModel('bastos', 3),
        CardModel('espadas', 2),
    ]


def test_bot_easy_prefers_first_valid_combo(monkeypatch):
    table = _make_table()

    one = CardModel('oros', 1)
    king = CardModel('oros', 12)
    seven = CardModel('oros', 7)

    bot = Bot('EasyBot', difficulty='easy')
    # Ensure bot will try the king first
    bot.hand = [king, one, seven]

    # Force easy mode NOT to miss by making random() return > 0.3
    monkeypatch.setattr(models.random, 'random', lambda: 0.9)

    played, captured = bot.choose_card_to_play(table)
    assert played == king
    # King (value 10) should capture the standalone 5 of copas
    assert captured == [CardModel('copas', 5)]


def test_bot_medium_prefers_most_cards():
    table = _make_table()

    one = CardModel('oros', 1)
    king = CardModel('oros', 12)
    seven = CardModel('oros', 7)

    bot = Bot('MedBot', difficulty='medium')
    bot.hand = [king, one, seven]

    played, captured = bot.choose_card_to_play(table)
    assert played == king
    # For the king, medium should pick the combination with most table cards: 3 (espadas) + 2 (espadas)
    assert captured == [CardModel('espadas', 3), CardModel('espadas', 2)]


def test_bot_hard_prefers_strategic_play():
    table = _make_table()

    one = CardModel('oros', 1)
    king = CardModel('oros', 12)
    seven = CardModel('oros', 7)

    # Place seven first so bot will attempt it and hard mode will evaluate combos
    bot = Bot('HardBot', difficulty='hard')
    bot.hand = [seven, king, one]

    played, captured = bot.choose_card_to_play(table)
    assert played == seven
    # Playing 7 (value 7) can capture a 3-card combo: 1 + 5 + 2 = 8
    assert captured == [CardModel('copas', 1), CardModel('copas', 5), CardModel('espadas', 2)]


def test_gamecontroller_start_and_play_turn():
    p1 = Player('Alice')
    p2 = Bot('Bot', difficulty='medium')
    gc = GameController([p1, p2])
    gc.start_game()

    # After start_game, players should have 3 cards each and table 4 cards
    assert len(p1.hand) == 3
    assert len(p2.hand) == 3
    assert len(gc.table_cards) == 4

    # Play a valid turn: player plays first card
    card = p1.hand[0]
    res = gc.play_turn(p1, card)
    assert res is True

    # Ensure turn advanced
    assert gc.current_player is p2


def test_escoba_awarded_when_table_cleared():
    bot = Bot('EscobaBot', difficulty='medium')
    other = Player('Other')
    gc = GameController([bot, other])

    # Prepare a table that will be fully captured by the bot's play
    table_card = CardModel('copas', 5)
    king = CardModel('oros', 12)

    bot.hand = [king]
    gc.table_cards = [table_card]
    gc.current_player_index = 0  # bot's turn

    res = gc.play_turn(bot, king, selected_table_cards=[table_card])
    assert res is True
    # After clearing the table, the bot should receive an escoba point
    assert bot.score['escobas'] == 1


def test_easy_intentional_miss(monkeypatch):
    table = _make_table()
    king = CardModel('oros', 12)
    bot = Bot('MissBot', difficulty='easy')
    bot.hand = [king]

    # Force the easy-mode intentional miss by patching models.random.random
    monkeypatch.setattr(models.random, 'random', lambda: 0.1)

    # can_capture should return [] due to intentional miss
    result = bot.can_capture(king, table, difficulty='easy')
    assert result == []

    # choose_card_to_play should then play the card but capture nothing
    played, captured = bot.choose_card_to_play(table)
    assert captured == []
if __name__ == '__main__':
    pytest.main(['-q'])