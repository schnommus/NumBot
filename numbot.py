## Seb Holzapfel 2012 - Schnommus
## Plays a numbers game over IRC
## Skeleton from MomBot code

import sys
from twisted.internet import reactor
from twisted.words.protocols import irc
from twisted.internet import protocol
import time
import random
import math
import string

def PickNumbers():
    #Possible numbers to choose from
    ns = range(1, 10) + [10, 25, 50, 75, 100]
    
    #Pick 6 at random and return them
    return [ ns[random.randint(0, len(ns)-1)] for n in range(0, 6) ]

def PickTarget(numbers):
    #Local copy because we're popping stuff
    numbers = numbers[:]

    #Possible operators
    operators = ['+','-','*','/']

    #Stores the solution that the computer uses as a string
    resultString = '(((('

    #Start by popping some random number
    currentTotal = numbers.pop(random.randint(0, len(numbers)-1))
    resultString += str(currentTotal)

    #Pick 3 others and do random (valid) operations.
    for n in range(0, 3):
        currentNumber = numbers.pop(random.randint(0, len(numbers)-1))
        currentOperator = ''
        while True:
            currentOperator = operators[random.randint(0, len(operators)-1)]
            if currentOperator == '+':
                if (currentTotal + currentNumber) < 1000:
                    currentTotal += currentNumber
                    break
            elif currentOperator == '-':
                if (currentTotal - currentNumber) > 0:
                    currentTotal -= currentNumber
                    break
            elif currentOperator == '*':
                if (currentTotal * currentNumber) < 1000:
                    currentTotal *= currentNumber
                    break
            elif currentOperator == '/':
                if (currentTotal % currentNumber) == 0:
                    currentTotal /= currentNumber
                    break
        resultString += ") " + currentOperator + " " + str(currentNumber)
    return (resultString, currentTotal)

class NumBot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.isActive = False
        self.join(self.factory.channel)
        self.leaderBoard = {}
        print "Signed on as %s." % (self.nickname,)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def privmsg(self, user, channel, msg):
        print "Recieved: " + msg

        if "!numbergame" in msg.lower():
            self.isActive = True
            self.currentLeader = ('',0)
            self.numbs = PickNumbers()
            self.msg( channel, "The numbers are: " + str(self.numbs))
            self.target = PickTarget(self.numbs)
            self.msg( channel, "The target is: " + str(self.target[1]) + ", You have 45 seconds...")
            self.end = reactor.callLater(45, self.privmsg, '', channel, "!endgame")

        if "!endgame" in msg.lower() and self.isActive:
            self.isActive = False
            if self.currentLeader[0] != '':
                self.msg( channel, self.currentLeader[0] + " has won on " + str(self.currentLeader[1]) + " points!" )
                try:
                    self.leaderBoard[self.currentLeader[0]] += 1
                except:
                    self.leaderBoard[self.currentLeader[0]] = 1
            else:
                self.msg( channel, "Nobody even tried..." )
            self.msg( channel, "My solution: " + str(self.target[0]) )

        if "!showlb" in msg.lower():
            if len(self.leaderBoard) > 0:
                self.msg( channel, "Scores are:" )
            else:
                self.msg( channel, "No-one has scored any points..." )
            c = self.leaderBoard.items()
            c.sort()
            for user, score in c[::-1]:
                self.msg( channel, user + ": " + str(score) )

        if "!clearlb" in msg.lower():
            self.leaderBoard = {}
            self.msg( channel, "Leaderboard cleared." )

        if self.isActive and "!a" in msg.lower():

            #Remove instruction and ignore all but digits + math characters
            s = msg.replace("!a", '')
            sa = ''.join([x for x in s if x in '0123456789()*/+-'])
            print sa
            #Remove all but numbers (to check later if they were in spec)
            sv = ''
            for c in sa:
                if c in '()*/+-':
                    sv += ' '
                else:
                    sv += c
                    
            vl = [int(x) for x in sv.split(" ") if x != '']

            #Check if numbers in spec
            iv = True
            for n in vl:
                if vl.count(n) > self.numbs.count(n):
                    iv = False
                    break

            #Get user name from user string
            u = user.split("!")[0]
            if iv:
                try:
                    result = eval(sa, {'__builtins__': None}, {})
                    points = 10-int(math.fabs(result-self.target[1]))
                    if points < 0:
                        points = 0
                    self.msg( channel, u + " - Answered " + str(result) + ", worth " + str(points) + " points." )
                    if self.currentLeader[1] < points:
                        self.currentLeader = (u, points)
                        self.msg( channel, u + " is new leader on " + str(points) + " points!" )
                        if points == 10:
                            self.end.cancel()
                            self.privmsg( '', channel, "!endgame" )
                except:
                    self.msg( channel, u + " - Syntax error / Invalid expression" )
            else:
                self.msg( channel, u + " - Numbers used that shouldn't be" )


class NumBotFactory(protocol.ClientFactory):
    protocol = NumBot

    def __init__(self, channel, nickname='NumBot'):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)

chan = "##ncss_challenge"

if __name__ == "__main__":
    reactor.connectTCP('irc.freenode.net', 6667, NumBotFactory(chan))
    reactor.run()
