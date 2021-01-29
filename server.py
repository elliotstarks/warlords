#**********************************************************
# Server
# Author : Elliot Starks
# Last Modified : Jan 14, 2014
# <Developed for CSCI367 @ WWU>
#**********************************************************

#!/user/bin/env python

import socket, select, sys, argparse
from util import Lobby, Player
import util, parser

if __name__ == "__main__":

    HOST = '' 
    SIZE = 4096   # Max size of messages
    
    # Default values, can be specified by user via cmd line
    timeout = 15
    minPlayers = 3
    countdown = 5#15
    
    # Create a socket on which to listen
    server = util.create_socket((HOST, util.PORT))
    
    readlist = [server]
    
    #********** Handle command line ***************
    
    parserObj = argparse.ArgumentParser()
    parserObj.add_argument('-t', type=int,\
                        help='Specify client timeout (seconds), default = 15')
    parserObj.add_argument('-m', type=int,\
                        help='Set minimum players (< 7), default = 3')
    parserObj.add_argument('-l', type=int,\
                        help='Specify lobby\'s countdown to game start, default = 15')
    args = parserObj.parse_args()
    
    # '-t' -> client timeout specified
    if args.t:
        timeout = args.t
        
    # '-m' -> minimum players specified
    if args.m:
        minPlayers = args.m
        
    # '-l' -> lobby game countdown specified
    if args.l:
        countdown = args.l
    
    # Create a lobby as defined
    lobby = Lobby(minPlayers, timeout, countdown)
    
    # Start listening for socket input
    running = 1 # Currently never set to 0
    while running:
        inready, outready, exready = select.select(readlist, [], [])
        
        # Service all input from players connecting/connected 
        for player in inready:
    
            # New client connecting -> initialize new player and add socket to readlist
            if player is server:
                socket, address = server.accept()
                newPlayer = Player(socket)
                readlist.append(newPlayer)
                print 'New client joined the server'
                
            # Otherwise get client input
            else:
                fullMsg = player.socket.recv(SIZE)
                
                # Input exists -> parse msg
                if fullMsg:

                    # Handle multiple messages
                    msgList = fullMsg.split('][')
                    msgNum = len(msgList)
                    # Add delimiters back in ***gotta be a better way***
                    if msgNum > 1:
                        for i in range(msgNum-1):
                            msgList[i] = msgList[i] + ']'
                            msgList[i+1] = '[' + msgList[i+1]

                    for msg in msgList:
                        print player.name + ': ' + msg
                        parser.parseClientMessage(lobby, player, msg)
        
                # No input means connection must be closed -> kill off client
                else:
                    # If this client was playing at a table -> set status to 'd'
                    if lobby.table:
                        if player in lobby.table.players:
                            lobby.table.players[lobby.table.players.index(player)].status = 'd' 
                    
                    # If client was in the lobby -> remove
                    if player in lobby.players:
                        lobby.remove(player)
                         
                    player.socket.close()
                    readlist.remove(player)
                    print 'A client disconnected'
            
            # Disconnect a player who has strikes = 3
            if lobby.isRemovePlayer:
                readlist.remove(player)
                lobby.isRemovePlayer = False
                print 'Player booted after striking out' 
    
    server.close()
    
