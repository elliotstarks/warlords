#**********************************************************
# Util : Defines various classes and methods to support
#        a server, lobby, table, players.
# Author : Elliot Starks
# Last Modified : Jan 30, 2014
# <Developed for CSCI367 @ WWU>
#**********************************************************

import socket, sys, time
from threading import Timer
from warlordsandscumbags import Game
import warlordsandscumbags

#!/user/bin/env python

MAX_CLIENTS = 42
PORT = 36722

#******************* General *************************
# Sets up a socket, binds to it, then listens
def create_socket(address):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(address)
    s.listen(MAX_CLIENTS)
    print 'Now listening at port ' + str(PORT)
    return s

# Grab waiting players from the lobby and start a table
def initTable(lobby):

    # Check to make sure we still have minimum players
    if lobby.num < lobby.minPlayers:
        return

    # Initialize a table and add to lobby
    table = Table()
    lobby.table = table
    
    # Move players to the table until full (7) or lobby is empty
    if len(lobby.players) > 0:
        tempList = lobby.players[:]
        for player in tempList:
            if table.num == 7:
                break
            table.add(player)
            lobby.remove(player)
        
    # Let the game begin!
    print 'Game table started with ' + str(table.num) + ' players.'
    lobbyMsg = '[slobb|' + str(lobby.num) + '|' + lobby.getPlayers() + ']'
    lobby.broadcast(lobbyMsg)
    table.initGame(lobby)

#************* Classes ************************************
        
# Lobby class, holds tables and players
class Lobby:    
    
    def __init__(self, minPlayers, timeout, countdown):
        self.table = None            # Hold the instance of the table
        self.players = []            # List of player objects in lobby
        self.num = 0                 # Number of players in lobby
        self.isRemovePlayer = False  # Player must be removed flag
        self.minPlayers = minPlayers # Minimum players needed to start game
        self.timeout = timeout       # Time in seconds players will timeout
        self.countdown = countdown   # Time in seconds the lobby will wait before starting game
        
    # Add a player to lobby
    def add(self, newPlayer):
        self.players.append(newPlayer)
        self.num += 1
    
    # Return string of players in proper format
    def getPlayers(self):
        playerStr = ''
        for player in self.players:
            playerStr += player.name + ','
        playerStr = playerStr[:-1]
        playerStr = '[' + playerStr + ']'
        return playerStr

    # Send a message to one player
    def sendClient(self, toPlayer, msg):
        toPlayer.socket.sendall(msg)
        
    # Broadcast a message to all players locally
    def broadcast(self, msg):
        for player in self.players:
            self.sendClient(player, msg)

    # Broadcast a message to all players globally
    def broadcastAll(self, msg):
        self.broadcast(msg)
        if self.table:
            for player in self.table.players:
                self.sendClient(player, msg) 
    
    # Checks for name uniqueness,
    #    True if unique
    #    False if duplicate found
    def isNameUnique(self, name):
        for player in self.players:
            if str(name.strip()) == str(player.name.strip()):
                return False
        return True
    
    # Remove player from lobby
    def remove(self, player):
        self.players.remove(player)
        self.num -= 1
        
    # Handles player timeouts
    #     --> strike player, force pass
    def handleTimeout(self, player):

        # Send strike message
        player.sendStrike(self, 20, False)

        # If this is the warlord mid-swap, rescind swap
        if self.table.swapCard is not None:
            self.table.players[0].hand.append(self.table.swapCard)
            self.table.players[self.table.num-1].hand.remove(self.table.swapCard)
            
        # Force pass
        self.table.currentPlayer.status = 'p'
        
        # If warlord mid-swap, send scumbag shand
        if self.table.swapCard:
            handMsg = '[shand|' + self.table.players[0].getHand() + ']'
            self.table.sendClient(self.table.players[0], handMsg)
            self.swapCard = None
             
        # Advance turn
        self.table.nextPlayer(self)
        
        
    # Check for valid play, None if valid, otherwise integer error code set
    def isValidPlay(self, fromPlayer, play):
        errorCode = None # Will hold the error code if not valid play

        # Quantity of cards in play >= stack?
        # If this play has a 2 (48-51) -> ignore quantity
        if not (48 <= int(play[0]) <= 51):
            tempStack = list(self.table.stack)
            tempStack[:] = [card for card in tempStack if not str(card) == '52']
            if len(play) < len(tempStack):
                errorCode = 13
        
        # If play > 1 card -> matching face values?
        elif len(play) > 1:
            suite = int(play[0]) / 4
            for card in play:
                if int(card) / 4 != suite:
                    errorCode = 11
                
        # Play face value >= stack?
        elif int(play[0]) < self.table.getStackMin(): 
            errorCode = 12

        return errorCode
    
    # Returns false if it is not fromPlayer's turn 
    def isTurn(self, fromPlayer):
        isTurn = True
        if fromPlayer.status is not 'a':
            isTurn = False
        return isTurn
    
    # Returns false if cards in play are not in fromPlayer's hand
    def isInHand(self, fromPlayer, play):
        isInHand = True
        for card in play:
            if int(card) not in fromPlayer.hand:
                isInHand = False
        return isInHand
    
    def handlePass(self, fromPlayer):
        # Set player status accordingly
        fromPlayer.status = 'p'
        self.table.nextPlayer(self)
        
        # Did all players but the last to play just pass?
        passCount = 0
        lastToPlay = None
        for player in self.table.players:
            if player.status is 'p' or player.out:
                passCount += 1
            else:
                lastToPlay = player
        # One player who has not passed -> now current player, start new round
        if passCount == (self.table.num - 1):
            self.table.currentPlayer = lastToPlay
            self.table.nextRound(self)

    # Handles valid plays, players out, and game ending *** BULKY ***
    def processPlay(self, fromPlayer, play):
        
        # Check for skip criteria:
        #    matching number and quantity of previous play
        fullPlay = list(play)
        play[:] = [card for card in play if not str(card) == '52']
        tempStack = list(self.table.stack)
        tempStack[:] = [card for card in tempStack if not str(card) == '52']
        
        # If we have a match -> 
        if len(play) == len(tempStack) and\
            int(play[0])/4 == int(tempStack[0])/4:
            self.table.skipNext = True 
        
        # If this play included the 3 of clubs -> toggle flag
        if '00' in play:
            self.table.game.isStartingGame = False
        
        # Update table stack and player hand
        self.table.stack = fullPlay
        for card in play:
            fromPlayer.hand.remove(int(card))
            fromPlayer.numCards -= 1
        sortedHand = sorted(fromPlayer.hand)
        fromPlayer.hand = sortedHand
        handMsg = '[shand|' + fromPlayer.getHand() + ']'
        self.table.sendClient(fromPlayer, handMsg)
        
        
        # Check to see if player is out,
        #    add to ranked players list and set out flag
        if len(fromPlayer.hand) == 0:
            self.table.rankedPlayers.append(fromPlayer)
            fromPlayer.out = True
            
            # Was this the second to last player to go out?
            #     Just end the hand, append scumbag to ranked list,
            #     start a new hand
            if len(self.table.rankedPlayers) >= (self.table.num - 1):
                for player in self.table.players:
                    if player.numCards > 0:
                        scumbag = player
                        break
                self.table.rankedPlayers.append(scumbag)
                self.nextHand()
                return
            
        # If a two (48-51) was played,
        #    reset stack, player goes again
        if 48 <= int(play[0]) <= 51:
            self.table.nextRound(self)
            return
        
        # Update player status, advance turn
        self.table.currentPlayer.status = 'w'
        self.table.nextPlayer(self)
        
    # Handles the advancement of hands *** BULKY ***
    def nextHand(self):
        
        print 'Starting new hand'
        # Assign new table seating based on rank
        self.table.players = self.table.rankedPlayers
        self.table.ranked = 0
        
        # Pull players from the lobby while <= max players (7),
        #     starting with the head of the list
        tempList = self.players[:]
        for player in tempList:
            if len(self.table.players) == 7:
                break
            self.table.add(player)
            self.remove(player)
        numPlayers = len(self.table.players)
        self.table.players.reverse()

        # Reset game attributes
        self.table.game.resetGame(numPlayers)
        self.table.game.initPlayers()

        # Reset table attributes
        self.table.rankedPlayers = []
        self.table.stack = [52, 52, 52, 52]
        
        # Reset player attributes
        for player in self.table.players:
            player.reset()
        
        # Get player hands dealt
        for i in range(0, self.table.num):
            self.table.players[i].hand = self.table.game.players[i].cards 
        
            # Don't send hand to scumbag
            if i == 0:
                continue
            else:
                # Send message showing hand to player 
                handMsg = '[shand|' + self.table.players[i].getHand() + ']'
                self.table.sendClient(self.table.players[i], handMsg)

            # Append scumbag's highest card to warlord cards,
            #    send swapw to warlord
            if i == (self.table.num - 1):
                swapCard = self.table.players[0].hand.pop()
                self.table.swapCard = swapCard
                self.table.players[i].hand.append(swapCard)
                swapMsg = '[swapw|' + str(swapCard) + ']'
                self.table.sendClient(self.table.players[i], swapMsg)

        tableMsg = '[stabl|' + self.table.getTableStatus() + '|'\
                    + self.table.getStack() + '|0]'
        self.table.broadcast(tableMsg)

        # Warlord goes first
        self.table.currentPlayer = self.table.players[self.table.num-1]
        self.table.currentPlayer.status = 'a'
        
        # TIMEOUTDEBUG
        # Start timeout on active player
#        self.table.timer = Timer(self.timeout, self.handleTimeout, [self.table.currentPlayer])
#        self.table.timer.start()
        
# Table class: where the game is played, inherits from Lobby
class Table(Lobby):
    def __init__(self):
        self.players = []               # List of players at table
        self.currentPlayer = None       # Player whose turn it is
        self.num = 0                    # Number of players
        self.stack = [52, 52, 52, 52]   # The middle stack
        self.game = None                # Instance of game
        self.ranked = 1                 # 1 if unranked, 0 if ranks established
        self.rankedPlayers = []         # Players who have gone out
        self.skipNext = False           # Flag to indicate if skipping a player
        self.swapCard = None            # Set to int of scumbag card gained
        self.timer = None               # Holds current instance of timeout timer
        
    # initializes a game     
    def initGame(self, lobby):
    
        game = Game(self.num)
        self.game = game
        game.initPlayers()
        
        # Get player hands dealt
        for i in range(0, self.num):
            self.players[i].hand = game.players[i].cards 
        
            # Send message showing hand to player 
            handMsg = '[shand|' + self.players[i].getHand() + ']'
            self.sendClient(self.players[i], handMsg)

        # Start the hand -> get whose turn, set to active
        turnIndex = game.newHand()
        self.currentPlayer = self.players[turnIndex]
        self.players[turnIndex].status = 'a'
        
        # Send initial table message
        tableMsg = '[stabl|' + self.getTableStatus() + '|'\
                    + self.getStack() + '|1]'
        self.broadcast(tableMsg)
    
        # TIMEOUTDEBUG
        # Start timeout on active player
#        self.timer = Timer(lobby.timeout, lobby.handleTimeout, [self.currentPlayer])
#        self.timer.start()
    
    def getStack(self):
        stackStr = ''
        for card in self.stack:
            stackStr += str(card) + ','
        stackStr = stackStr[:-1]
        return stackStr
    
    # Returns integer of lowest card value on the stack,
    #     -1 if empty
    def getStackMin(self):
        minCard = 52
        for card in self.stack:
            if int(card) < minCard:
                minCard = int(card)

        # Stack is empty
        if minCard == 52:
            minCard = -1
        return minCard

    def getTableStatus(self):
        
        tableStr = ''
        
        # Format players at table
        for player in self.players:
            tableStr += player.status + str(player.strikes) + ':'\
                      + player.name + ':' + (str(player.numCards)).zfill(2) + ','

        # Format empty spots at table
        for i in range(self.num, 7):
            tableStr += 'e0:        :00,'
        
        tableStr = tableStr[:-1]
        return tableStr
    
    # Handles the advancement of rounds
    def nextRound(self, lobby):
        
        self.stack = [52, 52, 52, 52]
        
        for player in self.players:
            handMsg = '[shand|' + player.getHand() + ']'
            self.sendClient(player, handMsg)
            
        tableMsg = '[stabl|' + self.getTableStatus() + '|'\
                    + self.getStack() + '|' + str(self.ranked) + ']'
        self.broadcast(tableMsg)
    
        # TIMEOUTDEBUG
        # Start timeout on active player
#        self.timer = Timer(lobby.timeout, lobby.handleTimeout, [self.currentPlayer])
#        self.timer.start()
    
    # Handles the advancement of player turns
    def nextPlayer(self, lobby):
        
        # Did the current player just strike out?
        playerToStrike = None
        if self.currentPlayer.strikes >= 3:
            playerToStrike = self.currentPlayer
  
        # Find next valid player
        while 1:
            # If 1 player left, end hand, attempt new hand
            if len(self.players) == 1:
                self.rankedPlayers.append(self.currentPlayer)
                lobby.nextHand()
                return
            nextIndex = self.players.index(self.currentPlayer) + 1
            if nextIndex == self.num:
                nextIndex = 0
            self.currentPlayer = self.players[nextIndex]
            if self.currentPlayer.out == False:
                break
        
        # If 2 players left, simply other player's turn
        playersLeft = []
        for player in self.players:
            if not player.out or not player.status == 'd':
                playersLeft.append(player)
        if len(playersLeft) == 2:
            self.skipNext = False
            for player in playersLeft:
                if player is not self.currentPlayer:
                    self.currentPlayer = player
                    break
            
        # If last play was matched -> skip player (force pass)
        if self.skipNext:
            self.skipNext = False
            self.currentPlayer.status = 'p'
            self.nextPlayer(lobby)
        else:
            self.currentPlayer.status = 'a'
            tableMsg = '[stabl|' + self.getTableStatus() + '|'\
                    + self.getStack() + '|' + str(self.ranked) + ']'
            self.broadcast(tableMsg)
        
        if playerToStrike:
            self.remove(playerToStrike)
            
        # TIMEOUTDEBUG
        # Start timeout on active player
#        self.timer = Timer(lobby.timeout, lobby.handleTimeout, [self.currentPlayer])
#        self.timer.start()
        
# Player class: wraps a socket with player attributes
class Player:
    def __init__(self, socket, name = 'new player'):
        socket.setblocking(0)
        self.socket = socket
        self.name = name
        self.hand = []
        self.numCards = 0
        self.strikes = 0
        self.status = 'w'
        self.out = False
        self.buffer = None

    # Need for socket wrap 
    def fileno(self):
        return self.socket.fileno()

    # Reset player attributes for next game
    def reset(self):
        self.status = 'w'
        self.out = False

    # Send this player a strike, handles kick if = 3
    def sendStrike(self, lobby, strikeCode, sendHand):
        
        self.strikes += 1
        strikeMsg = '[strik|' + str(strikeCode) + '|' + str(self.strikes) + ']'
        
        # Locate player, send message,
        #     if strikes = 3 -> Yuuurrrr Out!
        if self in lobby.players:
            lobby.sendClient(self, strikeMsg)
            if self.strikes == 3:
                lobby.remove(self)
                lobby.isRemovePlayer = True
                return
            # If flagged, resend player's hand
            if sendHand:
                handMsg = '[shand|' + self.getHand() + ']'
                lobby.sendClient(self, handMsg)
        elif lobby.table:
            if self in lobby.table.players:
                lobby.table.sendClient(self, strikeMsg)
                if self.strikes == 3:
                    lobby.table.currentPlayer.status = 'd'
                    lobby.table.nextPlayer(lobby)
                    lobby.isRemovePlayer = True
                    return
                # If flagged, resend player's hand
                if sendHand:
                    handMsg = '[shand|' + self.getHand() + ']'
                    lobby.table.sendClient(self, handMsg)
        else:
            print self.name + ' is in limbo, unable to strike.'
            return
        
        # If this is currentPlayer and timer going, reset timeout
        if lobby.table:
            if lobby.table.timer:
                if self is lobby.table.currentPlayer:
                    lobby.table.timer.cancel()
                    lobby.table.timer = Timer(lobby.timeout, lobby.handleTimeout, [self])
                    lobby.table.timer.start()
            
    # Parse the player's hand and return a string matching syntax
    def getHand(self):
        handStr = ''
        handLen = 0
        for card in self.hand:
            handStr += (str(card)).zfill(2) + ','
            handLen += 1
            
        self.numCards = handLen
        # Pad the hand with empty cards to make 18 total cards
        for empty in range(handLen, 18):
            handStr += '52,'
            
        handStr = handStr[:-1]
        return handStr
    
# Hold game info linked to client
class Client:
    def __init__(self):
        self.name = None
        self.hand = []
        self.numCards = 0
        self.strikes = 0
        self.status = 'w'
        self.stack = [52,52,52,52]
        self.ranked = 1

    def setGameInfo(self, gameInfo):

        # Set stack and ranked attributes
        self.stack = gameInfo[1].split(',')
        self.ranked = gameInfo[2]

        # Find my info
        found = False
        for i in range(7):
            if self.name == gameInfo[0][i][1]:
                print 'Found player: ' + self.name
                self.numCards = gameInfo[0][i][2]
                print 'Number of cards set: ' + self.numCards
                self.status = gameInfo[0][i][0][0]
                print 'Status set: ' + self.status
                self.strikes = gameInfo[0][i][0][1]
                print 'Number of strikes set: ' + self.strikes
                found = True
                break
        if not found:
            print 'Could not locate player ' + self.name + ' to update game info'
        
    
    # Returns integer of lowest card value on the stack,
    #     -1 if empty
    def getStackMin(self):
        minCard = 52
        for card in self.stack:
            if int(card) < minCard:
                minCard = int(card)

        # Stack is empty
        if minCard == 52:
            minCard = -1
        return minCard    
    
    # Simple AI for client auto-mode
    def autoTurn(self):
    
        stackVal = 0
        stackQty = 0
    
        # Active?
        if self.status is not 'a':
            return None
        
        # What card(s) to play?
        else:
            # Get stack value/quantity
            stackVal = self.getStackMin()
            for card in self.stack:
                if card != 52:
                    stackQty += 1
            
            # Find card(s) in hand to play
            currQty = 1
            currVal = -1
            for i in range(len(self.hand)):
    
                # Pass?
                if self.hand[i] == 52:
                    cardMsg = '52,52,52,52'
                    break
                
                # Play a two?
                if self.hand[i] >= 48:
                    cardMsg = str(self.hand[i]) + ',52,52,52'
                    break
                
                # Card value >= stack value
                if self.hand[i] > stackVal:
                    
                    # Card value matches current value
                    if self.hand[i]/4 == currVal:
                        currQty += 1
                    
                        # Minimum valid play found -> trivial ai
                        if currQty >= stackQty:
                            
                            # Aggregate string of playable cards
                            cardMsg = ''
                            for j in range(currQty):
                                cardMsg += str(self.hand[i-j]) + ','
                            for blank in range(4-currQty):
                                cardMsg += '52,'
                            cardMsg = cardMsg[:-1]
                            break
                        
                    # New card value
                    else:
                        currVal = self.hand[i]
                        currQty = 1
            
            # Return card message to send to server
            playMsg = '[cplay|' + cardMsg + ']'
            return playMsg 