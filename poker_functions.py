import numpy as np
import settings
import os

# Parameters that indicate which part of the game
# was used for Monte Carlo statistics
MC_BF_PREFLOP = "before preflop"
MC_PREFLOP = "preflop"
MC_4TH = "4th card reveal"
MC_FINAL = "final card reveal"

len_suits = len(settings.card_suits)
len_values = len(settings.card_values)

# ******** logging *********
def logging(rank, msg, displayMsg = True):

  # Stores logging into newest directory
  sim_dir = os.path.join(settings.main_logging_dir, get_latest_directory(settings.main_logging_dir))

  if displayMsg == True:
    print(msg)

  logging_file = "{}_{}.txt".format("logging", rank)
  dat = open(os.path.join(sim_dir, logging_file), "a")
  
  dat.write(msg + "\n")


def get_latest_directory(path):
    
  dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

  latest = sorted(dirs, key = lambda x: os.path.getctime(os.path.join(path, x)), reverse = True)[:1]

  return latest[0]
  
# ******** end logging *********
  
# ******** begin Players info functions **** 
# Returns array of players position at the table
# in relation to dealer's positions.
# Arguments are array of active players and dealer


def get_small_blind_player(players, dealer):

  if dealer == None :
    # First dealer is process ranked 0
    print("Dealer is not set!")
    return -1
    
  return get_next_player(dealer, players, pos_offset = 1)

def get_big_blind_player(players, dealer):
  
  if dealer == None :
    # First dealer is process ranked 0
    print("Dealer is not set!")
    return -1
    
  return get_next_player(dealer, players, pos_offset = 2)
      
def get_next_player(main_player, players, pos_offset = 1):

  # Gets player position in relation to main player.
  # pos_offset means number of positions between two players.
  if main_player == None:
    print("Main player is not set!")
    return -1
  elif len(players) == 0:
    print("There are no players!")
    return -1
  
  
  next_player = None

  i = 0

  while next_player == None:

    idx = 0
    if players[i] == main_player:
      idx = i
      found = False

      while found == False:

        if pos_offset == 0:
          found = True
          next_player = players[idx]
          
        elif idx + 1 > len(players) - 1:
          idx = 0
          
        else:
          idx += 1

        pos_offset -= 1
      
    else:      
      i += 1

      if i > len(players) - 1 and next_player == None:
        idx = np.where(main_player == players)

        if isinstance(players, tuple):
          print("///////////////players {} are tuple, main_player".format(players, main_player).upper())
        if idx == len(players) - 1:
          next_player = players[0]
        else:
          next_player = players[idx + 1]
          
  return next_player
      
def get_players_pos(players, dealer):

  dealer_index = None

  tmp = []
  for i in range(0, len(players)):
      
    if players[i] == dealer:
      dealer_index = i
      break
      
    else:
      tmp = np.append(tmp, players[i])

  if dealer_index < len(players):
    for i in range(len(players) - 1, dealer_index, -1):
    
      tmp = np.insert(tmp, 0, players[i])

  tmp = np.append(tmp, dealer)
      
  return np.array(tmp, dtype = np.int32)
  
def get_dealer(current_dealer, players):

  next_dlr = None
  
  if current_dealer == None :
    # First dealer is process ranked 0
    next_dlr = 0
    
  else:

    next_dlr = get_next_player(current_dealer, players, pos_offset = 1)
        
  return next_dlr

def get_other_players(main_player, all_players):

  if len(all_players) < 1:
    print("Nema drugih igrača!")
    exit(-1)
    
  other_players = []

  for i in range(0, len(all_players)):
    if all_players[i] != main_player:
      other_players.append(all_players[i])

  if len(other_players) < 1:
    return None
  else:    
    return other_players

def set_players_for_new_hand(send_money_info, recv_money_info, hand, size, rank):
  
  # Set all players and remove those that have no money
  players = np.arange(0, size, dtype = np.int32)

  for i in range(0, len(recv_money_info)):

    if recv_money_info[i][1] <= 0:

      logging(rank, "Player {} has no money to continue.".format(recv_money_info[i][0]))
      players = remove_player(players, recv_money_info[i][0])

  return players

def is_hand_won(recv_h_win_info, game_section, rank, pot, money):

  for i in range(0, len(recv_h_win_info)):
    if recv_h_win_info[i][1] > -1:

      if rank == recv_h_win_info[i][0]:
        logging(rank, "*** Player {} on {}  wins pot of amount {} $ and now has {} $ ***".format(recv_h_win_info[i][0], game_section, pot, money).upper())

      return True

  return False

def is_game_over(recv_info):

  for i in range(0, len(recv_info)):
    if recv_info[0][1] == 1:
      return True

  return False
      
# ******** end Players info functions ****
    
# Formulas for calculationg player actions
# ******** begin Player actions ********
def player_plays(chances):
  
  rand = np.random.random()

  if rand <= chances:
    return True
  else:
    return False
    
def player_folds(player, all_players):

  if len(all_players) < 1:
    print("Nema više igrača!")
    return -1
  elif player not in all_players:
    print("Krivi index igrača!")
    return -1
    
  for i in range(0, len(all_players)):
    if i == player:
      all_players = np.delete(all_players, i)
      break

  return all_players

def remove_player(all_players, player):

  if not player in all_players:
    print("Player {} not all_players array: {}!".format(player, all_players))
    return -1

  for i in range(0, len(all_players)):

    if all_players[i] == player:
      return np.delete(all_players, i)

def get_player_action(chances):

  rand = np.random.random()
  
  if rand <= chances:
    # Determine if player will raise only if chances are higher then settings.raise_chance_border
    if chances >= settings.raise_chance_border and rand >= (chances - settings.raise_chance):
      return settings.RAISE
    else:
      return settings.CHECK
  else:
    return settings.FOLD
    
# ******** end Player actions ***********

def final_card_betting(current_money, cards, bet_amount, invested_amount):

  # Calculates and turns each factor into float as percentage e.g. 34.123 = 0.34123
  x1 = get_player_success(current_money) * settings.final_x1
  x2 = ((hand_combination(cards) / settings.poker_hands["Royal Flush"]) * settings.final_x2)

  # Ratio of players curent money amount and bet amount
  x3 = (bet_amount / current_money) * settings.final_x3

  # Ratio of invested amount in current and amount that player had at the beginning of hand
  x4 = (invested_amount / (current_money + invested_amount)) * settings.final_x4

  result = (x1 + x2 - x3 + x4) 
  
  # print("\n    x1: {}, x2: {}, x3: {}, x4: {} = result: {}\n".format(x1, x2, x3, x4, result))
  
  return result

    
def forth_card_betting(current_money, cards, bet_amount, invested_amount):

  # Calculates and turns each factor into float as percentage e.g. 34.123 = 0.34123
  x1 = get_player_success(current_money) * settings.forth_x1
  x2 = ((hand_combination(cards) / settings.poker_hands["Royal Flush"]) * settings.forth_x2)

  # Ratio of players curent money amount and bet amount
  x3 = (bet_amount / current_money) * settings.forth_x3

  # Ratio of invested amount in current and amount that player had at the beginning of hand
  x4 = (invested_amount / (current_money + invested_amount)) * settings.forth_x4

  result = (x1 + x2 - x3 + x4) 
  
  # print("\n    x1: {}, x2: {}, x3: {}, x4: {} = result: {}\n".format(x1, x2, x3, x4, result))
  
  return result

  
def after_preflop_betting(current_money, cards, bet_amount, invested_amount):

  # Calculates and turns each factor into float as percentage e.g. 34.123 = 0.34123
  x1 = get_player_success(current_money) * settings.aft_pf_x1
  x2 = ((hand_combination(cards) / settings.poker_hands["Royal Flush"]) * settings.aft_pf_x2)

  # Ratio of players curent money amount and bet amount
  x3 = (bet_amount / current_money) * settings.aft_pf_x3

  # Ratio of invested amount in current and amount that player had at the beginning of hand
  x4 = (invested_amount / (current_money + invested_amount)) * settings.aft_pf_x4
  
  result = (x1 + x2 - x3 + x4) 
  
  # print("\n    x1: {}, x2: {}, x3: {}, x4: {} = result: {}\n".format(x1, x2, x3, x4, result))
  
  return result

  
def before_preflop_betting(current_money, deal_cards, other_players_money, invested_amount):

  # Calculates and turns each factor into float as percentage e.g. 34.123 = 0.34123
  x1 = get_player_success(current_money) * settings.bf_pf_x1
  x2 = ((hand_combination(deal_cards) / settings.poker_hands["Royal Flush"]) * settings.bf_pf_x2)
  # x3 = other_players_factor(other_players_money) * settings.preflop_other_players_strength
  x3 = best_player_factor(other_players_money) * settings.bf_pf_x3

  # Ratio of invested amount in current and amount that player had at the beginning of hand
  x4 = (invested_amount / (current_money + invested_amount)) * settings.bf_pf_x4
  
  result = (x1 + x2 - x3 + x4) 
  
  return result

def best_player_factor(other_players_money):

  return max(other_players_money) / settings.player_money_amount
  
def other_players_factor(other_players_money):

  result = 0.0

  for i in range(0 , len(other_players_money)):
    result += get_player_success(other_players_money[i])

  return result / len(other_players_money)
              
def get_player_success(current_money):

  return current_money / settings.player_money_amount


  
# ******** end Player actions ********

# ********* Begin card combinations ********
# First argument is numpy array cards for combination and
# second is boolean if function sums combination strength with card values in combination.
# It used to test whcih player has strongest combination if two players have same combination, 
def hand_combination(cards, sum_card_values = False):
  
  cards_sum = None

  # If true then this function returns combination strength + card values
  if sum_card_values == True:
    cards_sum = get_cards_sum(cards)
  else:
    cards_sum = 0
    
  if len(cards) == 2:
    if is_pair(cards) == True:     
      return settings.poker_hands["Pair"] + cards_sum
      
    else:
      return settings.poker_hands["High Card"] + cards_sum
  else:      

    combination = None
    
    if is_royal_flush(cards):
      combination = settings.poker_hands["Royal Flush"] + cards_sum
    elif is_straight_flush(cards):
      combination = settings.poker_hands["Straight Flush"] + cards_sum
    elif is_four_of_kind(cards):
      combination = settings.poker_hands["Four of a Kind"] + cards_sum
    elif is_full_house(cards):
      combination = settings.poker_hands["Full House"] + cards_sum
    elif is_flush(cards):
      combination = settings.poker_hands["Flush"] + cards_sum
    elif is_straight(cards):
      combination = settings.poker_hands["Straight"] + cards_sum
    elif is_three_of_kind(cards):
      combination = settings.poker_hands["Three of a Kind"] + cards_sum
    elif is_two_pair(cards):
      combination = settings.poker_hands["Two Pair"] + cards_sum
    elif is_pair(cards):
      combination = settings.poker_hands["Pair"] + cards_sum
    else:
      combination = settings.poker_hands["High Card"] + cards_sum

  return combination
  
def highest_card(cards):

  c_values = get_cards_values(cards)
  c_values = np.sort(c_values)[::-1]

  return c_values[0]
  
def is_four_of_kind(cards):

  c_values = get_cards_values(cards)

  for i in range(0, len(c_values)):
    count = 1
    for j in range(i + 1, len(c_values)):
      if c_values[i] == c_values[j]:
        count += 1

      if count >= 4:
        return True
        
  return False
        
def is_full_house(cards):
  
  c_values = get_cards_values(cards)
  three_of_kind = False
  
  for i in range(0, len(c_values) - 1):
    count = 1
    three_cards = [c_values[i]]
    
    for j in range(i + 1, len(c_values)):

      if c_values[i] == c_values[j]:
        count += 1
        three_cards.append(c_values[j])

      if count >= 3:
        three_of_kind = True
        break

    if three_of_kind == True:
      break
          
  if three_of_kind == True:
    for i in range(0, len(c_values) - 1):
      for j in range(i + 1, len(c_values)):

        if c_values[i] == c_values[j]:
          # If pair is not one of three of kind cards
          if c_values[i] not in three_cards:            
            return True
        
  return False
  
def is_royal_flush(cards):

  if is_straight(cards) and is_flush(cards):
    c_values = get_cards_values(cards)
    c_values = np.sort(c_values)[::-1]
    
    if np.sum(c_values[:5]) == 60:
      return True    
    
  return False
  
def is_straight_flush(cards):

  if is_straight(cards) and is_flush(cards):
    return True
    
  return False
  
def is_flush(cards):  

  c_suits = get_cards_suits(cards)

  for i in range(0, len(c_suits) - 1):
    count = 1
    
    for j in range(i + 1, len(c_suits)):
      
      if c_suits[i] == c_suits[j]:
        count += 1

      if count >= 5:
        return True
        
  return False

def is_straight(cards):

  c_values = get_cards_values(cards)
  c_values = np.sort(c_values)[::-1]

  for i in range(0, len(c_values) - 1):

    tmp1 = np.array(c_values[i:i+5], dtype = np.int32)

    if len(tmp1) < 5:
      break
      
    tmp2 = np.arange(tmp1[0], tmp1[len(tmp1) - 1], -1, dtype = np.int32) # 3rd arg is for descending array
    tmp2 = np.append(tmp2, tmp1[len(tmp1) - 1])  

    if np.array_equal(tmp1, tmp2) == True:
      return True
    
  return False
      
def is_pair(cards):

  c_values = get_cards_values(cards)
    
  if len(c_values) == 2:
    if c_values[0] == c_values[1]:      
      return True
      
  else:
    
    for i in range(0, len(c_values) - 1):
      for j in range(i + 1, len(c_values)):

        if c_values[i] == c_values[j]:
          return True
          
  return False

def is_three_of_kind(cards):

  c_values = get_cards_values(cards)
    
  for i in range(0, len(c_values) - 1):
    count = 1
    
    for j in range(i + 1, len(c_values)):

      if c_values[i] == c_values[j]:
        count += 1        
        
      if count >= 3:        
        return True
          
  return False

def is_two_pair(cards):

  count = 0
  for i in range(0, len(cards) - 1):
    for j in range(i + 1, len(cards)):
      # Compares elements on i and j position.
      # This syntax is used in lists and numpy arrays.
      if is_pair(cards[[i, j]]):
        count += 1

      if count >= 2:
        return True

  return False

# ********* End card combinations ********

# ******** Begin Card functions ****************
def get_cards_values(cards):

  if not isinstance(cards, np.ndarray):
    return cards % 100
    
  values = []
  
  for card in cards:
    values.append(card % 100)

  return values

def get_cards_suits(cards):

  if not isinstance(cards, np.ndarray):
    return cards - (cards % 100)
    
  suits = []

  for card in cards:
    suits.append(card - (card % 100))

  return suits

def get_cards_sum(cards):

  if not isinstance(cards, np.ndarray):
    print("Neispravan tip podatka!")
    return -1
  elif len(cards) < 1:
    print("Karte su prazne!")
    return -1
    
  c_sum = 0

  for i in range(0, len(cards)):
    c_sum += get_cards_values(cards[i])

  return c_sum

def royal_sum():

  royals = ["ace", "king", "queen", "jack", "ten"]

  s = 0
  for item in settings.card_values:
    if item in royals:
      s += settings.card_values[item]

  return s


def combination_name(combination_value):

  if combination_value > 99 and combination_value < 1000:
    combination_value = combination_value - (combination_value % 100)
      
  elif combination_value > 999 and combination_value < 10000:
    combination_value = combination_value - (combination_value % 1000)
      
  else:
    combination_value = combination_value - (combination_value % 10)

  for combination_name in settings.poker_hands:    
    value = settings.poker_hands[combination_name]
    
    if value == combination_value:      
      return combination_name
      
  return None


def card_names(cards):

  if not isinstance(cards, np.ndarray):
    print("Neispravan tip podatka!")
    return -1
  elif len(cards) < 1:
    print("Karte su prazne!")
    return -1

  names = []

  i = 0
  for card in cards:
  
    suit = card - (card % 100)
    value = card % 100

    suit_name = ""
    value_name = ""
    
    for item in settings.card_suits:
      if settings.card_suits[item] == suit:

        suit_name = item
        break

    for item in settings.card_values:
      if settings.card_values[item] == value:

        value_name = item
        break

    if len(suit_name) > 0 and len(value_name) > 0:
      names.append("{} of {}".format(value_name, suit_name))

  return names

def create_deck():

  cards = np.empty(len_suits * len_values, dtype=np.int32)
  
  i = 0
  
  for suit in settings.card_suits:
    
    for value in settings.card_values:

      cards[i] = settings.card_suits[suit] + settings.card_values[value]
      
      i += 1

  return cards

def shuffle(cards, shuffle_iter = 100):

  if not isinstance(cards, np.ndarray):
    print("Neispravan tip podatka!")
    return -1
  elif len(cards) < 1:
    print("Karte su prazne!")
    return -1
      
  for n in range(0, shuffle_iter):

      np.random.shuffle(cards)

  return 1


def deal(cards, n_cards = 2):

  if not isinstance(cards, np.ndarray):
    print("Neispravan tip podatka!")
    return -1
  elif len(cards) < 1:
    print("Karte su prazne!")
    return -1

  deal_cards = np.array([], dtype = np.int32)

  # Deals n cards (takes first n cards from deck)
  for i in range(0, n_cards):

    deal_cards = np.append(deal_cards, cards[i])
  
  # Removes first n cards from the deck  
  cards = np.delete(cards, np.s_[0:n_cards])

  return (cards, deal_cards)

# ******** End Card functions ****************

# ********* begin Other functions ***********

def is_all_in(money, investment):

  if investment >= money:
    return True
    
  return False
  
  
def turn_into_percent(number):

  if number < 1:
    return number
    
  tmp = str(number)
  divisor = 1

  for i in range(0, len(tmp)):
    if tmp[i] in [",", "."]:
      break
    else:
      divisor *= 10
  
  return number / divisor

  
# ********* end Other funcions **********
  
# *********** begin Pot functions *****

def bet(rank, amount, current_money):
  
  if amount >= current_money:
    amount = current_money

  current_money -= amount
  
  return amount, current_money
  
def raise_pot(pot, money, bet):

  if bet > money:
    bet = money
    
  pot = pot + bet
    
  money = money - bet

  if money < 0:
    money = 0
    
  return pot, money
    
# *********** end Pot functions ******

# *********** Monte Carlo Statistics functions ******

def set_statistics(mc_stat, cards):
    
  comb_value = (hand_combination(cards) // 100) - 1

  if comb_value >= 0:
    mc_stat[comb_value] += 1 # increment combination apperance
    mc_stat[len(mc_stat) - 1] += 1 # increment number of games
        
  return mc_stat
    
def get_log_statistics(mc_stat, mc_game_type):

  if mc_stat is None or len(mc_stat) == 0:
    return -1
    
  n_games = mc_stat[len(mc_stat) - 1] # last element is number of iterations
          
  comb_statistics = []
  comb_statistics.append("On {} in {} iterations: ".format(mc_game_type, n_games))
  
  # Iterate through each combination's number of appearances
  for i in range(0, len(mc_stat) - 1):

    comb_value = (i + 1) * 100
    comb_name = combination_name(comb_value)
    perc = round(mc_stat[i] / n_games, 2) * 100
    
    comb_statistics.append("   => {} appeared {} times --> {} %".format(comb_name, mc_stat[i], perc))

  return comb_statistics


def write_log_statistics(log_statistics, rank):

  for i in range(0, len(log_statistics)):

    logging(rank, log_statistics[i], displayMsg = False)
    