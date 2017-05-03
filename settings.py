# Number of plays. If this number is reached, then more than

# player has money. IN this case simulation is stopped.
n_iter = 100

# Amount of minimum bet at the beginning of the game.
# It is raised after n_bet_raise_iter iterations by double
min_bet = 2.00

# Number of iterations after minimum bet is raised
n_bet_raise_iter = 100

# How much each player has at the start of the game
player_money_amount = 100.00

# Card suits
card_suits = {
  "clubs" : 100,
  "diamonds" : 200,
  "hearts" : 300,
  "spades" : 400
  }

# Card values
card_values = {
  "two" : 2,
  "three" : 3,
  "four" : 4,
  "five" : 5,
  "six" : 6,
  "seven" : 7,
  "eight" : 8,
  "nine" : 9,
  "ten" : 10,
  "jack" : 11,
  "queen" : 12,
  "king" : 13,
  "ace" : 14,
}

high_card = "High Card"
pair = "Pair"
two_pair = "Two Pair"
three_kind = "Three of a Kind"
straight = "Straight"
flush = "Flush"
full_house = "Full House"
four_kind = "Four of a Kind"
straight_flush = "Straight Flush"
royal_flush = "Royal Flush"
n_hands = "Games"

# Combinations
poker_hands = {

  high_card : 100,
  pair : 200,
  two_pair : 300,
  three_kind : 400,
  straight : 500,
  flush : 600,
  full_house : 700,
  four_kind : 800,
  straight_flush : 900,
  royal_flush : 1000,  
}

FOLD = -1
CHECK = 2
CALL = 3
RAISE = 4


# Actions will be determined by chances that will be represented with number between 0 and 1. Random number will be used to determine if that number is lower or equal to chances value and if it is then action will be executed, otherwise it won't.
# This variable will be used when random number is lower or equal to chances then if random number is between interva [chances - raise_chance, chances_value], player will raise.
raise_chance = 0.1

# This number will be minimum chances value after which raise_chance value will be considered.
raise_chance_border = 0.75

# Before preflop -> factors used in before_preflop_betting function
# Importance of each factor that will be used for players decision before preflop () before dealer puts three cards faced up on table
bf_pf_x1 = 0.4
bf_pf_x2 = 5
bf_pf_x3 = 0.06
bf_pf_x4 = 6

# After preflop factor strength -> factors used in after_preflop_betting function
aft_pf_x1 = 0.3
aft_pf_x2 = 4
aft_pf_x3 = 0.06
aft_pf_x4 = 6

# Factors strength in forth_card_betting function that is used
# to calculate player chances for actions
forth_x1 = 0.25
forth_x2 = 4.2
forth_x3 = 0.06
forth_x4 = 5.5

# Factors strength in final_card_betting function that is used
# to calculate player chances for actions
final_x1 = 0.25
final_x2 = 4.2
final_x3 = 0.06
final_x4 = 5.5

main_logging_dir = "./Logging"
