#**********************************************************
# Client : TCP client
# Author : Elliot Starks
# Last Modified : Jan 25, 2014
# <Developed for CSCI367 @ WWU>
#**********************************************************

#!/usr/bin/env python

# ********Auto-mode notes********
# Client must get ALL game info from server messages!
# *******************************
import sys, socket, select, argparse, time
from util import Client
import parser, util

def prompt() :
    sys.stdout.write('\n% ')
    sys.stdout.flush()

if __name__ == "__main__":

    SIZE = 4096

    # Default values, can be specified by user via cmd line
    host = 'localhost'
    port = 36722
    name = None         # set name, otherwise must send 'cjoin' message
    manual = False      # mode: manual or automatic  

    #********** Handle command line ***************

    parserObj = argparse.ArgumentParser()
    parserObj.add_argument('-p', type=int,\
                        help='Specify a port to connect to, default = localhost')
    parserObj.add_argument('-n',\
                        help='Send server desired name')
    parserObj.add_argument('-s',\
                        help='Specify DNS or IP of the server to connect to, default = 36722')
    parserObj.add_argument('-m', action='store_true',\
                        help='flag : manual or automatic mode, default to auto')
    args = parserObj.parse_args()
    
    # '-p' -> port specified
    if args.p:
        port = args.p
    # '-n' -> name specified
    if args.n:
        name = args.n
    # '-s' -> DNS or IP specified
    if args.s:
        host = args.s
    # '-m' -> mode specified
    if args.m:
        manual = True 
                
    # Arguments set -> ready to connect to the server
    
    # Create a TCP/IPv4 socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect socket to the server port
    server_addr = (host, port)
    print >>sys.stderr, 'Connecting to server %s port %s' % server_addr
    s.connect(server_addr)
    
    client = Client()
    
    # If name specified -> send server the padded name
    if name:
        while len(name) < 8:
            name += ' '
        client.name = name
        nameMsg = '[cjoin|' + name + ']'
        s.send(nameMsg)
    
    socketList = [sys.stdin, s]
    
    prompt()
    
    # Monitor stdin, receive data from server
    while 1:
        inready, outready, exready = select.select(socketList, [], [])   
        for input in inready:
            
            # Server sent something
            if input == s:
                fullMsg = input.recv(SIZE)
                if not fullMsg:
                    print 'You were disconnected from the server'
                    sys.exit()
                else:
                    
                    # Manual mode -> print message
                    if manual:
                        sys.stdout.write(fullMsg)

                    # Auto mode -> parse message
                    else:
                        print 'Server sent: ' + fullMsg
                        
                        # Handle multiple messages
                        msgList = fullMsg.split('][')
                        msgNum = len(msgList)
                        # Add delimiters back in ***gotta be a better way***
                        if msgNum > 1:
                            for i in range(msgNum-1):
                                msgList[i] = msgList[i] + ']'
                                msgList[i+1] = '[' + msgList[i+1]

                        for msg in msgList:
                        
                            print msg
                            result = parser.parseServerMessage(msg)
                            if result:
                                
                                # Server accepted us -> parse client info
                                if result[0] == 'sjoin':
                                    client.name = (result[1])[:8]
                                    print 'Client name set to ' + client.name
                                
                                # Table message -> parse game info
                                elif result[0] == 'stabl':
                                    client.setGameInfo(result[1])
                                    play = client.autoTurn()
                                    if play:
                                        print 'Sending play to server: ' + play
                                        s.send(play)
    
    
                                # Hand message -> parse player hand
                                elif result[0] == 'shand':
                                    client.hand = result[1].split(',')
                                
                                # Swap message
                                elif result[0] == 'swapw':
                                    cswap = '[cswap|' + client.hand[0] + ']'
                                    s.send(cswap)    
                                
            # User entered a message
            else:
                msg = sys.stdin.readline()
                s.send(msg)
            prompt()
    
    s.close()
    
