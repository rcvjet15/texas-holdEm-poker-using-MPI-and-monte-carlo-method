# texas-holdEm-poker-using-MPI-and-monte-carlo-method
This is Texas HoldEm Poker Simulation written in python using MPI library (Message Passing Interface) and Monte Carlo method is used for statistics

<h2>How to run</h2>

1. Follow instructions for installing mpi4py library for python on [mpi4py.scipy.org](https://mpi4py.scipy.org/docs/usrman/install.html)
2. Enter command: ```mpirun -np <number_of_players> /path/to/simulation.py``` or if 
3. Be patient and wait until one player is left or game reaches maximum number of rounds set in settings.py
4. During simulation, directory named ```Logging/``` will be created at the same location as ```/path/to/simulation.py``` and in it directory named ```Simulation_<date_and_time_when_simulation_was_run>/``` will be created for each simulation that will contain files named ```logging_<player_index>.txt``` in which will be written logging for each player (process) during simulation

<h2>Files Description</h2>

There are three main files:
  1. simulation.py -> main python script which contains logic for poker game and each process runs this script with own parameters
  2. settings.py -> script where can game settings can be set like number of rounds, amount of money which every player has at beginning of the game, card values, suits values etc.
  3. poker_functions.py -> script that acts like library which contains functions that are called in simulation.py. It contains functions like logic for game logging, formulas for calcluating each player actions, creating card deck, card dealing etc.
  
  
