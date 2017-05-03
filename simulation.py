import numpy as np
from mpi4py import MPI
import settings
import poker_functions as pf
import os
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size < 2:

  print("At least two players are required!")
  exit()

elif size > 22:
  print("Max is 22 players!")
  exit(-1)

# Monte Carlo statistics. Each element represents poker combination
# from lowest to highest.
# Last element is number of games
mc_stat_bf_preflop = np.zeros(11, dtype = np.int32)
mc_stat_preflop = np.zeros(11, dtype = np.int32)
mc_stat_4th = np.zeros(11, dtype = np.int32)
mc_stat_final = np.zeros(11, dtype = np.int32)

if rank == 0:

  main_logging = settings.main_logging_dir
  FMT = "%d_%m_%Y_%H_%M_%S"  
  now = time.strftime(FMT)

  if not os.path.exists(main_logging):
    os.mkdir(main_logging)

  os.mkdir("{}/{}_{}".format(main_logging, "Simulation", now))
  pf.logging(rank,str(rank) + "tetst string")
  

players = np.arange(0, size, dtype = np.int32)

big_blind = settings.min_bet
small_blind = big_blind / 2

money = settings.player_money_amount
dealer = None

start_time = time.time()

comm.Barrier()

for hand in range(0, settings.n_iter):

# ************** Set players for next round **************
    
  # If any player lost all money, remove him from players array
  send_money_info = np.array([rank, money], dtype = np.int32)
  recv_money_info = np.zeros((size, 2), dtype = np.int32)

  # Each player sends array of two elements: 1. rank; 2. money amount
  comm.Allgather(send_money_info, recv_money_info)

  players = pf.set_players_for_new_hand(send_money_info, recv_money_info, hand, size, rank)
    
  game_over = -1
  if len(players) == 1 and rank == players[0]:
    pf.logging(rank, "******* Player {} is winner with amount of {} $ *******".format(players[0], money).upper())
    game_over = 1
    
  elif rank in players:
    pf.logging(rank, "Remaining players in {}. hand are: {}.".format(hand + 1, players))

  game_over_info = np.zeros((size, 2), dtype = np.int32)

  # Each process sends their rank and game over parameter. Only one process can
  # send game_over parameter with value of 1, where others will send -1
  comm.Allgather(np.array([rank, game_over], dtype = np.int32), game_over_info)

  if pf.is_game_over(game_over_info): break
  
  comm.Barrier()

  pot = 0
  invested_amount = 0 # how much player invested in each hand
  hand_winner = -1
  is_all_in = False
    
  pf.logging(rank, "<------ Hand number: {} ------>".format(hand + 1).upper())

  # ************** begin Small blind and big blind **************
  
  pf.logging(rank, "<------ Small and big blind betting ------>".upper())
  
  if hand % settings.n_bet_raise_iter == 0 and hand > 0:
    settings.min_bet *= 2.00
    big_blind = settings.min_bet
    small_blind = big_blind / 2

  dealer = pf.get_dealer(dealer, players)
  
  if rank in players:
    pf.logging(rank, "Big blind amount: {}, small blind amount: {}".format(big_blind, small_blind))    
    pf.logging(rank, "Dealer is player: {}".format(dealer))

    sb_player = pf.get_small_blind_player(players, dealer)
    bb_player = pf.get_big_blind_player(players, dealer)

  else:
    sb_player = None
    bb_player = None
    
  amount = 0
  
  if rank == sb_player:
    pf.logging(rank, "Small blind has now player {} and has to put in {} $.".format(rank, small_blind))

    amount = small_blind
    
  if rank == bb_player:
    pf.logging(rank, "Big blind has now player {} and has to put in {} $.".format(rank, big_blind))
        
    amount = big_blind
    
  invested_amount += amount

  if rank in players:
    # Automatically decreases money value by bet.  
    amount, money = pf.bet(rank, amount, money)
    
    if money == 0 and is_all_in == False:

      pf.logging(rank, "Player: {} goes all in with: {} $ on {} blind.".format(rank, amount, "small" if rank == sb_player else "big"))
      is_all_in = True
    
  pot += comm.allreduce(amount, op = MPI.SUM)

  if rank == bb_player:
    pf.logging(rank, "Player: {} after big blind has: {}".format(rank, money))

  if rank == sb_player:
    pf.logging(rank, "Player: {} after small blind has: {}".format(rank, money))

  if rank in players:
    pf.logging(rank, "   Pot amount after small and big blind is now {} $".format(pot).upper())

  # ************** end Small blind and big blind **************
    
  # ************** begin DEALING **************

  pf.logging(rank, "<------ DEALING ------>".upper())
  
  table_cards = None
  deal_cards = None
  
  # Sets players positions for dealing. Dealer will be last in array
  # so he is the last player to get cards and to play
  players = pf.get_players_pos(players, dealer)

  
  if rank == dealer:

    cards = pf.create_deck()
    if pf.shuffle(cards) < 1:
      print("Error while shuffling!")
      exit(-1)
    
    # Deals cards to each player that are still active
    for player in players:

      if player == dealer:
        break
          
      sendMsg = np.empty((1, 2), dtype = np.int32)

      # Deals two cards and removes them from deck
      cards, deal_cards = pf.deal(cards, n_cards = 2)

      sendMsg[0] = deal_cards
      
      comm.Send(sendMsg, dest = player)

      # Dealer deals cards to himself
      cards, deal_cards = pf.deal(cards)
  elif rank in players:
        
    recvMsg = np.empty((1, 2), dtype = np.int32)

    comm.Recv(recvMsg, source = dealer)
    
    deal_cards = np.array(recvMsg[0], dtype = np.int32)

  comm.Barrier()
  
  if rank in players:
    pf.logging(rank, "  Player: {} got cards: {}".format(rank, pf.card_names(deal_cards)))
  
#  ************** Monte Carlo statistics **************

  # Players without money have no cards
  # so statistics is not measured for them anymore
  if deal_cards is not None:
    mc_stat_bf_preflop = pf.set_statistics(mc_stat_bf_preflop, deal_cards)
      
  #  ************** end DEALING  **************

  if rank in players:
    combination = pf.hand_combination(deal_cards)

    # If player has pair
    if combination != None and combination == settings.poker_hands["Pair"]:
      pf.logging(rank, "Player: {} has: {} of {}".format(rank, pf.combination_name(combination), pf.card_names(deal_cards)))

  #  ************** Betting before preflop  **************

  pf.logging(rank, "<------ Betting before preflop ------>".upper())
  
  other_players = np.array(pf.get_other_players(rank, players))

  # Simulation od current player (rank) observing other players status (money)
  sendMsg = np.array(money, dtype = np.int32)

  other_players_money = np.empty(size, dtype = np.int32)

  # Each process sends to other processes current money status
  comm.Allgather(sendMsg, other_players_money)

  """if len(other_players_money) > 1:
    for i in range(0, len(other_players_money)):

      if other_players_money[i] > 0 and i != rank:
        pf.logging(rank, "Main player: {} => Player: {} has: {} $".format(rank, i, other_players_money[i]))
  else:
    print("Process: " , rank, " didn't get message!")
    exit(-1)"""

  # Remove observer from other players money for calculations
  other_players_money = np.delete(other_players_money, rank)

  amount = 0

  folds = False

  
  if rank in players and is_all_in == False:
    chances = pf.before_preflop_betting(money, deal_cards, other_players_money, invested_amount)
    
    # Each player must bet big blind amount to stay in game
    if pf.player_plays(chances) == True:
      
      if rank == sb_player:
        amount = big_blind - small_blind
      
      elif rank != bb_player:
        amount = big_blind

      invested_amount += amount
    else:
    
      folds = True
    
  comm.Barrier()

  if rank in players:
    amount, money = pf.bet(rank, amount, money)

    if money == 0 and is_all_in == False:
      pf.logging(rank, "Player: {} goes all in with: {} $ before preflop.".format(rank, amount))
      is_all_in = True
      
  pot += comm.allreduce(amount, op = MPI.SUM)
  
  if amount > 0:    
    pf.logging(rank, 'Player {} calls {} $ and now has {} $'.format(rank, amount, money))

  if rank in players:
    pf.logging(rank, "   Pot amount after betting before preflop is now {} $".format(pot).upper())
  
  # Checks if any player folds. Each player sends array of length = 2
  # where first element is player rank and second player action, CHECK or FOLD.
  action_info = np.array([rank, settings.FOLD if folds == True else settings.CHECK], dtype = np.int32)

  recv_action_info = np.empty((size, 2), dtype = np.int32)
  
  comm.Allgather(action_info, recv_action_info)

  for i in range(0, len(recv_action_info)):
    if recv_action_info[i][0] in players:
      # If any player folds, exclude him from players array
      if recv_action_info[i][1] == settings.FOLD:
      
        players = pf.remove_player(players, recv_action_info[i][0])

        pf.logging(rank, 'Player {} folds before preflop.'.format(recv_action_info[i][0]))
      
        # If only one player remained
        if len(players) == 1:
          if rank == players[0]: # remaining player takes all pot
            money += pot

            hand_winner = rank
            break
      else:

        pf.logging(rank, 'Player {} checks before preflop.'.format(recv_action_info[i][0]))
      
  # Wait all processes to receive and process action_info from other processes
  comm.Barrier()

  # Each process sends to the others hand_winner value. If any process sends
  # hand_winner value greater than -1 then every process will skip this hand 
  h_win_info = np.array([rank, hand_winner], dtype = np.int32)
  recv_h_win_info = np.zeros((size, 2), dtype = np.int32)
  comm.Allgather(h_win_info, recv_h_win_info)

  # If any player won, skip this hand and deal another hand.
  if pf.is_hand_won(recv_h_win_info, "before preflop", rank, pot, money) == True: continue

  if rank in players:
    pf.logging(rank, "Remaining players before preflop are {}".format(players))
  
  #  ************** Facing up three cards aka Preflop  **************

  pf.logging(rank, "<------ Preflop ------>".upper())


  if rank == dealer:

    # Before preflop, top card is "destroyed"
    cards = np.delete(cards, np.s_[0] )
    cards, table_cards = pf.deal(cards, n_cards = 3)
    
  else:
    table_cards = np.zeros(3, dtype = np.int32)

  # All players now see preflop cards
  comm.Bcast(table_cards, root = dealer)

  if rank in players:
    pf.logging(rank, "Cards on preflop are {}".format(pf.card_names(table_cards)))

  if rank in players:

    comb_cards = np.concatenate((deal_cards, table_cards), axis = 0)
    combination = pf.hand_combination(comb_cards)

    if combination != None and combination > settings.poker_hands["High Card"]:

      pf.logging(rank, "Player {} on preflop has combination {} with cards in hand {}".format(rank, pf.combination_name(combination), pf.card_names(deal_cards)))

#  ************** Monte Carlo statistics **************

  # Players without money have no cards
  # so statistics is not measured for them anymore
  if deal_cards is not None:
    mc_stat_preflop = pf.set_statistics(mc_stat_preflop, np.concatenate((deal_cards, table_cards), axis = 0))

  
  bet_amount = 0
  bet_raised = True  

  comm.Barrier()
  
  # Actions on preflop
  # Loop while bets are being raised
  while bet_raised == True:

    # Each player will send 1D array with three elements -> 1. rank; 2. action (fold, raise or check); 3. bet_amount (in case if any player raises)
    action_info = np.zeros(3, dtype = np.int32)
    recv_action_info = np.zeros((size, 3), dtype = np.int32)
      
    # Loop through players and check if any player wants to raise
    for player in players:

      if rank == player:        

        if is_all_in == False:
          chances = pf.after_preflop_betting(money, comb_cards, bet_amount, invested_amount)
        
          pf.logging(rank, "    Player: {} has: {} % to play".format(rank, round(chances, 2) * 100))

          action = pf.get_player_action(chances)

          if action == settings.FOLD:
            
            action_info = np.array([rank, settings.FOLD, 0], dtype = np.int32)
            bet_raised = False

          else: # action == settings.CHECK:
                        
            action_info = np.array([rank, settings.CHECK, 0], dtype = np.int32)
            bet_raised = False            

          """else:
            bet_amount += big_blind
            action_info = np.array([rank, settings.RAISE, bet_amount], dtype = np.int32)"""
            # bet_raised = True
            
        # Players that are all in always check  
        else:
          action_info = np.array([rank, settings.CHECK, 0], dtype = np.int32)
          bet_raised = False
          
    comm.Allgather(action_info, recv_action_info)
    
    if rank not in players:
      break
  
    for i in range(0, len(recv_action_info)):

      if recv_action_info[i][0] in players:
        # If any player folds, exclude him from players array
        if recv_action_info[i][1] == settings.FOLD:
      
          players = pf.remove_player(players, recv_action_info[i][0])

          pf.logging(rank, 'Player {} folds on preflop.'.format(recv_action_info[i][0]))
      
          # If only one player remained
          if len(players) == 1:
            if rank == players[0]: # remaining player takes all pot
              money += pot

              hand_winner = rank
              break  
          
        else: # if recv_action_info[i][1] == settings.CHECK:

          pf.logging(rank, "Player {} checks on preflop.".format(recv_action_info[i][0]))

        """else:
          bet_raised = False
          bet_amount += big_blind"""
          
  comm.Barrier()

  # Each process sends to the others hand_winner value. If any process sends
  # hand_winner value greater than -1 then every process will skip this hand 
  h_win_info = np.array([rank, hand_winner], dtype = np.int32)
  recv_h_win_info = np.zeros((size, 2), dtype = np.int32)
  comm.Allgather(h_win_info, recv_h_win_info)
  
  # If any player won, skip this hand and deal another hand.
  if pf.is_hand_won(recv_h_win_info, "preflop", rank, pot, money) == True: continue
  
  if rank in players:
    pf.logging(rank, "Remaining players after preflop are {}".format(players))
    
      
  #  ************** Facing up 4th card  **************

  pf.logging(rank, "<------ 4th card reveal ------>".upper())
  
  if rank == dealer:

    # Before revealing 4th card, top card is "destroyed"
    cards = np.delete(cards, np.s_[0] )
    cards, forth_card = pf.deal(cards, n_cards = 1)    
    table_cards = np.append(table_cards, forth_card)

    pf.logging(rank, "Forth card is: {}".format(pf.card_names(forth_card)))
  else:
    table_cards = np.zeros(4, dtype = np.int32)

  comm.Bcast(table_cards, root = dealer)

  if rank in players:

    pf.logging(rank, "On table are now {}".format(pf.card_names(table_cards)))
    
    comb_cards = np.concatenate((deal_cards, table_cards), axis = 0)
    combination = pf.hand_combination(comb_cards)

    if combination != None and combination > settings.poker_hands["High Card"]:

      pf.logging(rank, "Player {} on 4th card reveal has combination {} with cards in hand {}".format(rank, pf.combination_name(combination), pf.card_names(deal_cards)))

  #  ************** Monte Carlo statistics **************

  # Players without money have no cards
  # so statistics is not measured for them anymore
  if deal_cards is not None:
    mc_stat_4th = pf.set_statistics(mc_stat_4th, np.concatenate((deal_cards, table_cards), axis = 0))

      
  bet_amount = 0
  bet_raised = True  

  comm.Barrier()
  
  # Actions on 4th card reveal
  # Loop while bets are being raised
  while bet_raised == True:

    # Each player will send 1D array with three elements -> 1. rank; 2. action (fold, raise or check); 3. bet_amount (in case if any player raises)
    action_info = np.zeros(3, dtype = np.int32)
    recv_action_info = np.zeros((size, 3), dtype = np.int32)
      
    # Loop through players and check if any player wants to raise
    for player in players:

      if rank == player:        

        if is_all_in == False:
          chances = pf.forth_card_betting(money, comb_cards, bet_amount, invested_amount)
        
          pf.logging(rank, "    Player: {} has: {} % to play".format(rank, round(chances, 2) * 100))

          action = pf.get_player_action(chances)

          if action == settings.FOLD:
            
            action_info = np.array([rank, settings.FOLD, 0], np.int32)
            bet_raised = False

          else:
                        
            action_info = np.array([rank, settings.CHECK, 0], np.int32)
            bet_raised = False
            
        else:
          action_info = np.array([rank, settings.CHECK, 0], dtype = np.int32)
          bet_raised = False
        
    comm.Allgather(action_info, recv_action_info)
    
    if rank not in players:
      break
      
    for i in range(0, len(recv_action_info)):

      if recv_action_info[i][0] in players:
        # If any player folds, exclude him from players array
        if recv_action_info[i][1] == settings.FOLD:
      
          players = pf.remove_player(players, recv_action_info[i][0])

          pf.logging(rank, 'Player {} folds on 4th card reveal.'.format(recv_action_info[i][0]))
      
          # If only one player remained
          if len(players) == 1:
            if rank == players[0]: # remaining player takes all pot
              money += pot

              hand_winner = rank
              break
        else:

          pf.logging(rank, "Player {} checks on 4th card reveal.".format(recv_action_info[i][0]))

  comm.Barrier()

  # Each process sends to the others hand_winner value. If any process sends
  # hand_winner value greater than -1 then every process will skip this hand 
  h_win_info = np.array([rank, hand_winner], dtype = np.int32)
  recv_h_win_info = np.zeros((size, 2), dtype = np.int32)
  comm.Allgather(h_win_info, recv_h_win_info)
   
  # If any player won, skip this hand and deal another hand.
  if pf.is_hand_won(recv_h_win_info, "4th card reveal", rank, pot, money) == True: continue
  
  if rank in players:
    pf.logging(rank, "Remaining players after 4th card reveal are {}".format(players))

  #  ************** Facing up 5th (final) card **************

  pf.logging(rank, "<------ Final card reveal ------>".upper())

  
  if rank == dealer:

    # Before revealing final card, top card is "destroyed"
    cards = np.delete(cards, np.s_[0] )
    cards, final_card = pf.deal(cards, n_cards = 1)    
    table_cards = np.append(table_cards, final_card)

    pf.logging(rank, "Final card is: {}".format(pf.card_names(final_card)))
  else:
    table_cards = np.zeros(5, dtype = np.int32)

  comm.Bcast(table_cards, root = dealer)

  if rank in players:
    pf.logging(rank, "On table are now {}".format(pf.card_names(table_cards)))

  if rank in players:

    comb_cards = np.concatenate((deal_cards, table_cards), axis = 0)
    combination = pf.hand_combination(comb_cards)

    if combination != None and combination > settings.poker_hands["High Card"]:

      pf.logging(rank, "Player {} on final card reveal has combination {} with cards in hand {}".format(rank, pf.combination_name(combination), pf.card_names(deal_cards)))

  #  ************** Monte Carlo statistics **************

  # Players without money have no cards
  # so statistics is not measured for them anymore
  if deal_cards is not None:
    mc_stat_final = pf.set_statistics(mc_stat_final, np.concatenate((deal_cards, table_cards), axis = 0))

    
  bet_amount = 0
  bet_raised = True  

  comm.Barrier()
  
  # Actions on final card reveal
  # Loop while bets are being raised
  while bet_raised == True:

    # Each player will send 1D array with three elements -> 1. rank; 2. action (fold, raise or check); 3. bet_amount (in case if any player raises)
    action_info = np.zeros(3, dtype = np.int32)
    recv_action_info = np.zeros((size, 3), dtype = np.int32)
      
    # Loop through players and check if any player wants to raise
    for player in players:

      if rank == player:        

        if is_all_in == False:
          chances = pf.final_card_betting(money, comb_cards, bet_amount, invested_amount)
        
          pf.logging(rank, "    Player: {} has: {} % to play".format(rank, round(chances, 2) * 100))

          action = pf.get_player_action(chances)

          if action == settings.FOLD:
            
            action_info = np.array([rank, settings.FOLD, 0], np.int32)
            bet_raised = False

          else:
                        
            action_info = np.array([rank, settings.CHECK, 0], np.int32)
            bet_raised = False
            
        else:
          action_info = np.array([rank, settings.CHECK, 0], dtype = np.int32)
          bet_raised = False
          
    comm.Allgather(action_info, recv_action_info)
    
    if rank not in players:
      break
        
    for i in range(0, len(recv_action_info)):

      if recv_action_info[i][0] in players:
        # If any player folds, exclude him from players array
        if recv_action_info[i][1] == settings.FOLD:
      
          players = pf.remove_player(players, recv_action_info[i][0])

          pf.logging(rank, 'Player {} folds on final card reveal.'.format(recv_action_info[i][0]))
      
          # If only one player remained
          if len(players) == 1:
            if rank == players[0]: # remaining player takes all pot
              money += pot

              hand_winner = rank
              break
        else:

          pf.logging(rank, "Player {} checks on final card reveal.".format(recv_action_info[i][0]))

  comm.Barrier()

  # Each process sends to the others hand_winner value. If any process sends
  # hand_winner value greater than -1 then every process will skip this hand 
  h_win_info = np.array([rank, hand_winner], dtype = np.int32)
  recv_h_win_info = np.zeros((size, 2), dtype = np.int32)
  comm.Allgather(h_win_info, recv_h_win_info)
      
  # If any player won, skip this hand and deal another hand.
  if pf.is_hand_won(recv_h_win_info, "final card reveal", rank, pot, money) == True: continue

  if rank in players:
    pf.logging(rank, "Remaining players after final card reveal are {}".format(players))

#  ************** Summary **************

  pf.logging(rank, "<------ Summary ------>".upper())
  
  if rank in players:

    comb_cards = np.concatenate((deal_cards, table_cards), axis = 0)
    
    # Sums combination value with every card's value except lowest card in player's hands.
    # If two players have pair and player 1 has ace and 2 and player has 8 and 7
    # then for combination value, player 1's ace and player 2's 8 used in sum.
    # Player with highest value is winner.
    # Even if two or more players have same combination, player with highest card is winner
    # because that player has higher total value
    combination_value = pf.hand_combination(comb_cards, sum_card_values = True) - min(pf.get_cards_values(deal_cards))

  else:
    combination_value = 0

  send_summary_info = np.array([rank, combination_value], dtype = np.int32)
  recv_summary_info = np.zeros((size, 2), dtype = np.int32)

  comm.Allgather(send_summary_info, recv_summary_info)

  max_val = 0
  winner = -1
  for i in range(len(recv_summary_info)):

    if recv_summary_info[i][1] > max_val:
      max_val = recv_summary_info[i][1]
      winner = recv_summary_info[i][0]
  
  if winner > -1 and rank == winner:

    money += pot      
    pf.logging(rank, "*** Player {} in {}. hand wins pot of amount {} $ and now has {} $".format(winner, hand + 1, pot, money).upper())
  
  comm.Barrier()

  if rank == 1:
    money = 0

  pf.logging(rank, "===> after {}. hand, player {} has {} $ <===".format(hand + 1, rank, money).upper())
    
end_time = time.time()

pf.logging(rank, "Simulation for process {} lasted for {} seconds.".format(rank, end_time - start_time))

pf.logging(rank, "\n<------ Monte Carlo Statistics ------>".upper())

log_stat_bf_pr = pf.get_log_statistics(mc_stat_bf_preflop, pf.MC_BF_PREFLOP)
log_stat_pr = pf.get_log_statistics(mc_stat_preflop, pf.MC_PREFLOP)
log_stat_4th = pf.get_log_statistics(mc_stat_4th, pf.MC_4TH)
log_stat_final = pf.get_log_statistics(mc_stat_final, pf.MC_FINAL)

pf.write_log_statistics(log_stat_bf_pr, rank)
pf.write_log_statistics(log_stat_pr, rank)
pf.write_log_statistics(log_stat_4th, rank)
pf.write_log_statistics(log_stat_final, rank)