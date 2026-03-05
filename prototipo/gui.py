import sys, pygame
import Card
import Deck
import Player
import Bot

pygame.init()

def check_sum(cards):
    total_sum = 0
    for card in cards:
        total_sum += card.value
    if total_sum == 15:
        return True
    return False

def sum_invalid():
    popup_surf = pygame.Surface((500, 200))
    popup_surf.fill((200, 200, 200))  # fondo gris claro
    popup_rect = popup_surf.get_rect()
    popup_rect.center = (width//2, height//2)
    pygame.draw.rect(popup_surf, (0, 0, 0), popup_rect, 3)  # borde negro

    # Fuente
    font = pygame.font.SysFont(None, 36)
    text = font.render("La suma de las cartas debe ser 15.", True, (0, 0, 0))
    text_rect = text.get_rect(center=popup_rect.center)

    return popup_surf, popup_rect, text, text_rect




size = width, height = 1920, 1080
speed = [0, 0]
black = 0, 0, 0

screen = pygame.display.set_mode(size)

background = pygame.image.load('assets/tapete.png').convert()
clock = pygame.time.Clock()            #get a pygame clock object

# Variables de arrastre
dragging = False
offset_x = 0
offset_y = 0

pop_up = None
pop_up_flag = False
display = False

player = Player.Player()
player_played = False
bot = Bot.Bot()
waiting = False

def display_score(title_rect):
    # for card, i in zip(player.scored_cards, range(1, player.scored_cards.__len__()+1)):
    #     print(f"SCORED: {card.value}, {card.suite}")
    #     card.image = pygame.transform.scale(card.image, (50, 75))
    #     card.rect.center = (pop_up_rect.left + 20 + i*10, pop_up_rect.top + 150 + i//5*20)
    font = pygame.font.SysFont(None, 36)
    cards_text = font.render(f"Cartas: {player.name if player.scored_cards.__len__() > bot.scored_cards.__len__() else bot.name}", True, (0, 0, 0))
    cards_text_rect = text.get_rect(center=(title_rect.centerx, title_rect.top + 100))
    screen.blit(cards_text, cards_text_rect)

    golds_text = font.render(f"Oros: {player.name if player.golds() > bot.golds() else bot.name} ({player.golds if player.golds() > bot.golds() else bot.golds()})", True, (0, 0, 0))
    golds_text_rect = text.get_rect(center=(cards_text_rect.centerx, cards_text_rect.top + 100))
    screen.blit(golds_text, golds_text_rect)

    sevens_text = font.render(f"Sevens: {player.name if player.sevens() > bot.sevens() else bot.name}", True, (0, 0, 0))
    sevens_text_rect = text.get_rect(center=(golds_text_rect.centerx, golds_text_rect.top + 100))
    screen.blit(sevens_text, sevens_text_rect)

    gold_seven_text = font.render(f"Golden seven: {player.name if player.has_golden_seven() else bot.name}", True, (0, 0, 0))
    gold_seven_text_rect = text.get_rect(center=(sevens_text_rect.centerx, sevens_text_rect.top + 100))
    screen.blit(gold_seven_text, gold_seven_text_rect)

    player_broom = font.render(f"Player brooms: {player.broom}", True, (0, 0, 0))
    player_broom_rect = text.get_rect(center=(gold_seven_text_rect.centerx, gold_seven_text_rect.top + 100))
    screen.blit(player_broom, player_broom_rect)

    bot_broom = font.render(f"Player brooms: {bot.broom}", True, (0, 0, 0))
    bot_broom_rect = text.get_rect(center=(player_broom_rect.centerx, player_broom_rect.top + 100))
    screen.blit(bot_broom, bot_broom_rect)



def init_game():
    global deck
    # deck = None
    deck = Deck.Deck()
    # deck.start()
    deck.shuffle()
    player.reset()
    bot.reset()
    player_cards, ai_cards = deck.deal()
    for card in player_cards:
        player.cards.add(card)
        print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
    for card in ai_cards:
        card.image = pygame.image.load(f"assets/scaled_negativo.png")
        bot.cards.add(card)
        print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
    player.reposition_player_cards()
    bot.reposition_bot_cards()
    deck.reposition_deck_cards()

    # Fuente
    font = pygame.font.SysFont(None, 36)
    deck_text = font.render(f"Cartas del mazo: {deck.all_cards.__len__()}", True, (0, 0, 0))
    deck_text_rect = deck_text.get_rect(center=(deck.rect.centerx, deck.rect.bottom + 20))
    
deck = Deck.Deck()
deck.shuffle()
player_cards, ai_cards = deck.deal()
for card in player_cards:
    player.cards.add(card)
    print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
for card in ai_cards:
    card.image = pygame.image.load(f"assets/scaled_negativo.png")
    bot.cards.add(card)
    print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
player.reposition_player_cards()
bot.reposition_bot_cards()
deck.reposition_deck_cards()

# Fuente
font = pygame.font.SysFont(None, 36)
deck_text = font.render(f"Cartas del mazo: {deck.all_cards.__len__()}", True, (0, 0, 0))
deck_text_rect = deck_text.get_rect(center=(deck.rect.centerx, deck.rect.bottom + 20))

# player_card = Card.Card(1, "GOLD", pygame.image.load("scaled.png"), (width//2, 4*height//5))

# table_cards = [Card.Card(10, "GOLD", pygame.image.load("scaled.png"), (width//5, height//2)), 
            #    Card.Card(5, "GOLD", pygame.image.load("scaled.png"), (2*width//5, height//2)), 
            #    Card.Card(4, "GOLD", pygame.image.load("scaled.png"), (3*width//5, height//2)), 
            #    Card.Card(2, "GOLD", pygame.image.load("scaled.png"), (4*width//5, height//2))]

while True:
    # Movimiento con flechitas    
    # keys = pygame.key.get_pressed()
    # for event in pygame.event.get():
    #     if event.type == pygame.QUIT: sys.exit()
        
    # if player_card.rect.top > 0:
    #     if keys[pygame.K_UP]:
    #         player_card.rect.move_ip(0, -5)
    # if player_card.rect.bottom < height:
    #     if keys[pygame.K_DOWN]:
    #         player_card.rect.move_ip(0, 5)
    # if player_card.rect.left > 0:
    #     if keys[pygame.K_LEFT]:
    #         player_card.rect.move_ip(-5, 0)
    # if player_card.rect.right < width:
    #     if keys[pygame.K_RIGHT]:
    #         player_card.rect.move_ip(5, 0)
    keys = pygame.key.get_pressed()

    if deck.all_cards or player.cards or bot.cards:
        if not player.cards and not bot.cards:
            player_cards, ai_cards = deck.draw()
            for card in player_cards:
                player.cards.add(card)
                print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
            for card in ai_cards:
                card.image = pygame.image.load(f"assets/scaled_negativo.png")
                bot.cards.add(card)
                print(f"[DEBUG] CARTA OBTENIDA: valor {card.value}, palo {card.suite}")
    else:
        for card in deck.drawn_cards:
            if player.scored:
                print("PAL PLAYER")
                player.scored_cards.add(card)
            else:
                print("PAL BOT")
                bot.scored_cards.add(card)
            deck.drawn_cards.remove(card)
        pop_up = pygame.Surface((1250, 800))
        pop_up.fill((200, 200, 200))  # fondo gris claro
        pop_up_rect = pop_up.get_rect()
        pop_up_rect.center = (width//2, height//2)
        pygame.draw.rect(pop_up, (0, 0, 0), pop_up_rect, 3)  # borde negro

        # Fuente
        font = pygame.font.SysFont(None, 36)
        text = font.render("Presiona R para volver a empezar.", True, (0, 0, 0))
        text_rect = text.get_rect(center=(pop_up_rect.centerx, pop_up_rect.top + 100))
    
        # display_score(text_rect)

        # print("CARTAS OROS 7S 7OROS")
        
        # print(player.scored_cards.__len__())
        # print(bot.scored_cards.__len__())
        cards_text = font.render(f"Cartas: {player.name if player.scored_cards.__len__() > bot.scored_cards.__len__() else bot.name} ({player.scored_cards.__len__() if player.scored_cards.__len__() > bot.scored_cards.__len__() else bot.scored_cards.__len__()})", True, (0, 0, 0))
        cards_text_rect = cards_text.get_rect(center=(text_rect.centerx, text_rect.top + 100))

        # print(player.golds())
        # print(bot.golds())
        golds_text = font.render(f"Oros: {player.name if player.golds() > bot.golds() else bot.name} ({player.golds() if player.golds() > bot.golds() else bot.golds()})", True, (0, 0, 0))
        golds_text_rect = golds_text.get_rect(center=(cards_text_rect.centerx, cards_text_rect.top + 100))

        # print(player.sevens())
        # print(bot.sevens())
        sevens_text = font.render(f"Sietes: {player.name if player.sevens() > bot.sevens() else bot.name}", True, (0, 0, 0))
        sevens_text_rect = sevens_text.get_rect(center=(golds_text_rect.centerx, golds_text_rect.top + 100))

        # print(player.has_golden_seven())
        # print(bot.has_golden_seven())
        gold_seven_text = font.render(f"Siete de velos: {player.name if player.has_golden_seven() else bot.name}", True, (0, 0, 0))
        gold_seven_text_rect = gold_seven_text.get_rect(center=(sevens_text_rect.centerx, sevens_text_rect.top + 100))

        player_broom = font.render(f"Escobas de Player: {player.broom}", True, (0, 0, 0))
        player_broom_rect = text.get_rect(center=(gold_seven_text_rect.centerx, gold_seven_text_rect.top + 100))

        bot_broom = font.render(f"Escobas de Bot: {bot.broom}", True, (0, 0, 0))
        bot_broom_rect = text.get_rect(center=(player_broom_rect.centerx, player_broom_rect.top + 100))

        pop_up_flag = True
        display = True



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        # Inicia el arrastre si haces clic sobre la carta
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            dummy = pygame.sprite.Sprite()
            dummy.rect = pygame.Rect(mouse_x, mouse_y, 1, 1)
            if player.cards:
                clicked_cards = pygame.sprite.spritecollide(dummy, player.cards, False)
                if clicked_cards:
                    clicked_card = clicked_cards[0]
                    clicked_card.drag_card()
                    offset_x = clicked_card.rect.x - mouse_x
                    offset_y = clicked_card.rect.y - mouse_y

            if deck.drawn_cards:
                clicked_cards = pygame.sprite.spritecollide(dummy, deck.drawn_cards, False)
                if clicked_cards:
                    card = clicked_cards[0]
                    if card.selected:
                        card.unselect_card()
                    else:
                        card.select_card()
                    
            if pop_up_flag:
                pop_up_flag = False

        # Mueve la carta mientras arrastras
        elif event.type == pygame.MOUSEMOTION:
            for card in player.cards:
                if card.is_dragging():
                    mouse_x, mouse_y = event.pos
                    card.rect.x = mouse_x + offset_x
                    card.rect.y = mouse_y + offset_y

        # Suelta la carta
        elif event.type == pygame.MOUSEBUTTONUP:
            for card in player.cards:
                if card.is_dragging():
                    if card.rect.y < height//2:
                        selected_cards = [card for card in deck.drawn_cards if card.selected]
                        if selected_cards:
                            selected_cards.append(card)
                            if check_sum(selected_cards):
                                player.cards.remove(card)
                                # table_cards = [card for card in table_cards if not card.selected]
                                for table_card in deck.drawn_cards:
                                    if table_card.selected:
                                        deck.drawn_cards.remove(table_card)
                                        player.scored_cards.add(table_card)
                                player.scored_cards.add(card)
                                player_played = True
                                bot.scored = False
                                player.scored = True
                                print("PLAYER PUNTUA")
                                if not deck.drawn_cards:
                                    player.broom+=1

                            else:
                                pop_up, pop_up_rect, text, text_rect = sum_invalid()
                                pop_up_flag = True
                                for card in player.cards:
                                    if card.is_dragging():
                                        card.undrag_card()
                        else:
                            player.cards.remove(card)
                            deck.drawn_cards.add(card)
                            player_played = True

                    else:
                        for card in player.cards:
                            if card.is_dragging():
                                card.undrag_card()

        elif keys[pygame.K_r] and pop_up_flag:
            init_game()
            pop_up_flag = False
            display = False

        # elif keys[pygame.K_UP]:
        #     print("KEY UP")
        #     deck.draw_one()

        # elif keys[pygame.K_DOWN]:
        #     print("KEY UP")
        #     new_card = deck.draw_player()
        #     player.cards.add(new_card)
        #     new_card.position = (width//2, 4*height//5)
        #     new_card.rect.center = (width//2, 4*height//5)

    if player_played:
        current_time = pygame.time.get_ticks()
        if not waiting:
            start_time = current_time
            waiting = True
        elif waiting and current_time - start_time >= 1000:  # 1000 ms = 1 segundo
            bot.play(deck, screen)
            waiting = False
            player_played = False
            if bot.scored:
                print("BOT PUNTUA")
                player.scored = False



    screen.blit(background, (0,0)) #erase
    # for card in table_cards:
    #     if card:
    #         screen.blit(card.image, card.rect)
    if deck.drawn_cards:
        deck.reposition_deck_cards()
        deck.drawn_cards.draw(screen)
    if player.cards:
        player.reposition_player_cards()
        player.cards.draw(screen)
    if bot.cards:
        bot.reposition_bot_cards()
        bot.cards.draw(screen)
    if pop_up_flag:
        screen.blit(pop_up, pop_up_rect)
        screen.blit(text, text_rect)
    if display:
        screen.blit(cards_text, cards_text_rect)
        screen.blit(golds_text, golds_text_rect)
        screen.blit(sevens_text, sevens_text_rect)
        screen.blit(gold_seven_text, gold_seven_text_rect)
        screen.blit(player_broom, player_broom_rect)
        screen.blit(bot_broom, bot_broom_rect)
            

    screen.blit(deck.image, deck.rect)
    deck_text = font.render(f"Cartas del mazo: {deck.all_cards.__len__()}", True, (255, 255, 255))
    screen.blit(deck_text, deck_text_rect)

    pygame.display.flip()
    clock.tick(60)                     #update 60 times per second