#**********************************************************
# Warlords and Scumbags (a.k.a. Presidents and Assholes),
#    Handles game utilities
# Author : Elliot Starks
# Last Modified : Jan 30, 2014
# <Developed for CSCI367 @ WWU>
#**********************************************************

import sys, random

#!/user/bin/env python

# An instance of a game of warlords and scumbags with numPlayers initialized
class Game:
    def __init__(self, numPlayers):
        
        # Our deck of cards, where:
        # 3 < 4 < 5 .. < K < A < 2
        #-------------------------------------------
        # 00 = 3 of clubs    .. 48 = 2 of clubs
        # 01 = 3 of diamonds .. 49 = 2 of diamonds
        # 02 = 3 of hearts   .. 50 = 2 of hearts
        # 03 = 3 of spades   .. 51 = 2 of spades
        #-------------------------------------------
        #            52 = no card 
        self.cards = [i for i in range(53)]
        self.players = []

        self.numPlayers = numPlayers    # Initialized via parameter passed
        self.isStartingRound = True     # Ranks established? (true = no rank)
        self.isStartingGame  = True     # If true -> first play = 3 of clubs (00)
    
    def resetGame(self, numPlayers):

        self.cards = [i for i in range(53)]
        self.players = []
        self.numPlayers = numPlayers
        self.isStartingRound = False
        self.isStartingGame = False
    
    def initPlayers(self):
        
        # Initialize players
        for i in range(0, self.numPlayers):
            gamePlayer = GamePlayer()
            self.players.append(gamePlayer)
        
        # Set hand sizes
        self.handSize()
        
        # Deal each player their hand
        for player in self.players:
            self.initHand(player)
            
    # Calculate hand size *** Currently hardcoded ***
    #    Preferential to higher ranking players
    #    (in the spirit of the game)
    def handSize(self):
        
        if self.numPlayers == 3:
            self.players[0].num = 18
            self.players[1].num, self.players[2].num = (17,)*2
        elif self.numPlayers == 4:
            self.players[0].num, self.players[1].num,\
            self.players[2].num, self.players[3].num = (13,)*4 
        elif self.numPlayers == 5:
            self.players[0].num, self.players[1].num = (11,)*2
            self.players[2].num, self.players[3].num, self.players[4].num = (10,)*3 
        elif self.numPlayers == 6:
            self.players[0].num, self.players[1].num,\
            self.players[2].num, self.players[3].num = (9,)*4
            self.players[4].num, self.players[5].num = (8,)*2
        elif self.numPlayers == 7:
            self.players[0].num, self.players[1].num, self.players[2].num = (8,)*3
            self.players[3].num, self.players[4].num,\
            self.players[5].num, self.players[6].num = (7,)*4
        else:
            print 'Something went wrong: numPlayers = ' + str(self.numPlayers)
            return
    
    # Deals a player their hand 
    def initHand(self, player):
        
        while len(player.cards) != player.num:
            cardDealt = random.randint(0,51)
            if cardDealt in self.cards:
                player.cards.append(cardDealt)
                self.cards.remove(cardDealt)
            else:
                self.initHand(player)
        
        # Initial hand sort
        sortedCards = sorted(player.cards)
        player.cards = sortedCards
    
    # Handles the start of a new hand, 
    #    return index of current player turn            
    def newHand(self):
        
        # Default to warlord (highest indexed player)
        indexOfPlayer = self.numPlayers-1
        
        # This is our first round -> 3 of clubs starts
        if self.isStartingRound:

            # Who has it?
            for player in self.players:
                if 00 in player.cards:
                    indexOfPlayer = self.players.index(player)
        return indexOfPlayer
    
# Simple player class
#     Might be redundant - inherit from table.player or eliminate?
class GamePlayer:
    def __init__(self):
        self.cards = []
        self.num = 0
        