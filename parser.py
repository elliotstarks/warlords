#************************************************************
# parser : message parsing utility for warlords and scumbags
# Author : Elliot Starks
# Last Modified : Jan 30, 2014
# <Developed for CSCI367 @ WWU>
#************************************************************

import sys, re, random
from threading import Timer
from util import Player, Lobby
import util

#!/user/bin/env python

# Handle server messages
def parseServerMessage(msg):
    
    msg = msg.rstrip('\n')

    # Parse the message with regular expressions
    patternTabl = re.compile(r'[\[](?P<cmd>\w{5})[\|](?P<status0>\w\d)[\:](?P<name0>[\w\W]{8})[\:](?P<num0>\d{2})[\,](?P<status1>\w\d)[\:](?P<name1>[\w\W]{8})[\:](?P<num1>\d{2})[\,](?P<status2>\w\d)[\:](?P<name2>[\w\W]{8})[\:](?P<num2>\d{2})[\,](?P<status3>\w\d)[\:](?P<name3>[\w\W]{8})[\:](?P<num3>\d{2})[\,](?P<status4>\w\d)[\:](?P<name4>[\w\W]{8})[\:](?P<num4>\d{2})[\,](?P<status5>\w\d)[\:](?P<name5>[\w\W]{8})[\:](?P<num5>\d{2})[\,](?P<status6>\w\d)[\:](?P<name6>[\w\W]{8})[\:](?P<num6>\d{2})[\|](?P<stack>[\d,]{11})[\|](?P<ranked>\d)[\]]')
    matchTabl = patternTabl.match(msg)
    patternBoth = re.compile(r'[\[](?P<cmd>\w{5})[\|](?P<msg>[\w\W]+)[\]]$')
    matchBoth = patternBoth.match(msg)
    
    if matchTabl:
        matchTabl.groupdict()
        command = matchTabl.group('cmd')
        stack = matchTabl.group('stack')
        ranked = matchTabl.group('ranked')
        status0 = matchTabl.group('status0')
        name0 = matchTabl.group('name0')
        num0 = matchTabl.group('num0')
        status1 = matchTabl.group('status1')
        name1 = matchTabl.group('name1')
        num1 = matchTabl.group('num1')
        status2 = matchTabl.group('status2')
        name2 = matchTabl.group('name2')
        num2 = matchTabl.group('num2')
        status3 = matchTabl.group('status3')
        name3 = matchTabl.group('name3')
        num3 = matchTabl.group('num3')
        status4 = matchTabl.group('status4')
        name4 = matchTabl.group('name4')
        num4 = matchTabl.group('num4')
        status5 = matchTabl.group('status5')
        name5 = matchTabl.group('name5')
        num5 = matchTabl.group('num5')
        status6 = matchTabl.group('status6')
        name6 = matchTabl.group('name6')
        num6 = matchTabl.group('num6')
        message = [[[status0, name0, num0], [status1, name1, num1], [status2, name2, num2], [status3, name3, num3], [status4, name4, num4], [status5, name5, num5], [status6, name6, num6]], stack, ranked]
    elif matchBoth:
        matchBoth.groupdict()
        command = matchBoth.group('cmd')
        message = matchBoth.group('msg')    

    # Bad server syntax
    else:
        print 'Server syntax error'
        return
    
    # Return cmd, msg tuple to client for processing
    if command == 'sjoin':
        return [command, message]
    elif command == 'stabl':
        return [command, message]
    elif command == 'swapw':
        return [command, message]
    elif command == 'shand':
        return [command, message]
    else:
        return None

# Handle client messages
def parseClientMessage(lobby, fromPlayer, fullMsg):

    # Maximum length of accepted message syntax
    maxLen = 71
    maxJoin = 8
    maxChat = 63
    maxPlay = 11
    maxSwap = 2
    
    # Strip of newline characters
    fullMsg = fullMsg.rstrip('\n')

    # Handle multiple messages
    msgList = fullMsg.split('][')
    msgNum = len(msgList)
    if msgNum > 1:
        for i in range(1, msgNum):
            if i % 2 == 0:
                msgList[i-1] = '[' + msgList[i-1]
            else:
                msgList[i-1] = msgList[i-1] + ']'
    for msg in msgList:             
    
        # Enforce max message length, send strike
        if len(msg) > maxLen:
            fromPlayer.sendStrike(lobby, 32, False)
    
        # Parse the message with regular expressions
        patternBoth = re.compile(r'^[\[](?P<cmd>\w{5})[\|](?P<msg>[\w\W]+)[\]]$')
        matchBoth = patternBoth.match(msg)
        patternPlay = re.compile(r'^[\[](?P<cmd>\w{5})[\|](?P<msg>(\d+,?)+(\d+)?)[\]]')
        matchPlay = patternPlay.match(msg)
        patternCmd = re.compile(r'^[\[](?P<cmd>\w{5})[\]]')
        matchCmd = patternCmd.match(msg)
        patternPart1 = re.compile(r'[\[][\w\W]*')
        matchPart1 = patternPart1.match(msg)
        patternPart2 = re.compile(r'[\w\W]*[\]]')
        matchPart2 = patternPart2.match(msg)
        command = None
        message = None
    
        if matchBoth:
            matchBoth.groupdict()
            command = matchBoth.group('cmd')
            message = matchBoth.group('msg')
        elif matchPlay:
            command = matchPlay.group('cmd')
            message = matchPlay.group('msg')
        elif matchCmd:
            matchCmd.groupdict()
            command = matchCmd.group('cmd')
            
        # Potential partial message
        elif matchPart1:
            fromPlayer.buffer = msg
            return
        # Potential partial message tail
        elif matchPart2:
            if fromPlayer.buffer:
                message = fromPlayer.buffer + msg
                fromPlayer.buffer = None
                parseClientMessage(lobby, fromPlayer, message)
            else:
                fromPlayer.sendStrike(lobby, 30, False)
            return
        # Bad client syntax
        else:
            # Send client strike message
            fromPlayer.sendStrike(lobby, 30, False)
            return
        
        # Call function based on command to parse the message,
        #     handles syntax length strikes
        if command == 'cjoin':
            if len(message) > maxJoin:
                fromPlayer.sendStrike(lobby, 32, False)
                return
            cjoin(lobby, fromPlayer, message)
        elif command == 'cchat':
            if len(message) > maxChat:
                fromPlayer.sendStrike(lobby, 32, False)
                return
            cchat(lobby, fromPlayer, message)
        elif command == 'cplay':
            if not message:
                fromPlayer.sendStrike(lobby, 30, False)
                return
            if len(message) != maxPlay:
                fromPlayer.sendStrike(lobby, 32, False)
                return
            cplay(lobby, fromPlayer, message)
        elif command == 'chand':
            chand(lobby, fromPlayer)
        elif command == 'cswap':
            if len(message) > maxSwap:
                fromPlayer.sendStrike(lobby, 32, False)
                return
            cswap(lobby, fromPlayer, message)


# cmd = cjoin -> parse client  *** THIS IS BULKY! ***   
def cjoin(lobby, newPlayer, name):

    # Process the name:    
    # Strip name of any evil non-legal-C-name characters *** NEED NO LEADING NUMBER ***
    name = re.sub('[^A-Za-z0-9_]+', '', name) 
    # Check for name uniqueness
    isUnique = lobby.isNameUnique(name)
    if isUnique:
        # Pad the name to 8 characters with whitespace
        while len(name) < 8:
            name += ' '
    else:
        # Mangle the name to be unique
        newName = name.strip()
        if len(newName) >= 6:
            name = name[:-3]
            name += str(random.randint(100,999))
        else:
            for i in range(3):
                newName += str(random.randint(0,9))
            name = newName
        while len(name) < 8:
            name += ' ' # ***Loop back around if not isNameUnique***
            
    # Send a message to the client with their name
    joinMsg = '[sjoin|' + name + ']'
    lobby.sendClient(newPlayer, joinMsg)
    
    # Add newPlayer to our player list
    newPlayer.name = name[:8]
    lobby.add(newPlayer)
    
    # Broadcast informing the lobby players of a new player
    if lobby.num is not 0:
        lobbyMsg = '[slobb|' + str(lobby.num) + '|' + lobby.getPlayers() + ']'
        lobby.broadcast(lobbyMsg)
    
    # Minimum players reached -> start timer, then start table
    if lobby.num >= lobby.minPlayers:
        countdown = Timer(lobby.countdown, util.initTable, [lobby])
        countdown.start()

# Handle client chat messages
def cchat(lobby, fromPlayer, msg):
    
    # Pad the message with whitespace to 63 characters
    while len(msg) < 63:
        msg += ' '
        
    # Send chat message to lobby AND table
    msg = '[schat|' + fromPlayer.name + '|' + msg + ']'
    lobby.broadcastAll(msg)

# Handle client request to display their hand
def chand(lobby, fromPlayer):
    
    handMsg = '[shand|' + fromPlayer.getHand() + ']'
    lobby.sendClient(fromPlayer, handMsg)
    
# Handle client play requests
def cplay(lobby, fromPlayer, msg):
    
    # Player sitting at a table?
    if fromPlayer in lobby.players:
        fromPlayer.sendStrike
        (lobby, 31, False)
        return

    # Out of turn?
    if not lobby.isTurn(fromPlayer):
        # Send strike message
        fromPlayer.sendStrike(lobby, 15, True)
        return

    # Parse the string and generate a list of cards in play
    play = msg.split(',')
    fullPlay = list(play)
    play[:] = [card for card in play if not str(card) == '52']

    # Pass?
    if not play:
        # If no ranking, game starting -> play needs 00, can't pass
        if lobby.table.game.isStartingGame:
            # Send strike message
            fromPlayer.sendStrike(lobby, 18, True)
            return
        # Otherwise, handle the pass    
        lobby.handlePass(fromPlayer)
        return
    
    # If no ranking, game starting -> play must include 3 of clubs (00)
    if lobby.table.game.isStartingGame:
        if '00' not in play:
            fromPlayer.sendStrike(lobby, 16, True)
            return
    
    # Duplicate cards?
    if len(play) != len(set(play)):
        # Send strike message
        fromPlayer.sendStrike(lobby, 17, True)
        return
    
    # In player's hand?
    if not lobby.isInHand(fromPlayer, play):
        # Send strike message
        fromPlayer.sendStrike(lobby, 14, True)
        return

    # Valid play?
    returnCode = lobby.isValidPlay(fromPlayer, play)
    if returnCode is not None:
        # Send strike message
        fromPlayer.sendStrike(lobby, returnCode, True)
        return
    
    # No return code set -> valid play
    else:
        if lobby.table.timer:
            lobby.table.timer.cancel()
            lobby.table.timer = None
        lobby.processPlay(fromPlayer, fullPlay)
        return

# Handle swap request     
def cswap(lobby, fromPlayer, message):

    # Sent from player at table?
    if lobby.table:
        if fromPlayer not in lobby.table.players:
            fromPlayer.sendStrike(lobby, 31, False)
            return
    # No table exists
    else:
        fromPlayer.sendStrike(lobby, 31, False)
        return
             
    # Sent from warlord?
    if fromPlayer is not lobby.table.players[lobby.table.num-1]:
        fromPlayer.sendStrike(lobby, 71, False)
        return
    
    # Sent out of turn?
    if not lobby.table.swapCard:
        fromPlayer.sendStrike(lobby, 72, False)
        return
        
    # In player's hand?
    if int(message) not in fromPlayer.hand:
        fromPlayer.sendStrike(lobby, 70, True)
        return
    
    # Valid swap message, send scumbag swaps, shand
    if lobby.table.timer:
        lobby.table.timer.cancel()
        lobby.table.timer = None
    swapMsg = '[swaps|' + message + '|' + str(lobby.table.swapCard) + ']'
    lobby.table.sendClient(lobby.table.players[0], swapMsg)
    lobby.table.swapCard = None
    handMsg = '[shand|' + lobby.table.players[0].getHand() + ']'
    lobby.table.sendClient(lobby.table.players[0], handMsg)
    tableMsg = '[stabl|' + lobby.table.getTableStatus() + '|'\
            + lobby.table.getStack() + '|0]'
    lobby.table.broadcast(tableMsg)