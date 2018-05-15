#!/usr/bin/env python3

"""

Play Johanne's family solitaire

h for help

Controls should be obvious (arrow keys + enter) except for:
 [r] deal a round of cards
 [s] put the discard pile back into the cards to draw from

Version: 0.1

Malte Lau Petersen
maltelau@protonmail.com
May 2018
"""

from typing import List, Dict, Tuple
from collections import namedtuple

import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from itertools import count
import random
import sys

import logging

######################################
# Logging

logger = logging.getLogger()
#handler = logging.StreamHandler()
handler = logging.FileHandler('kabale.log')
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)



######################################
# text

HELP_LINES = 80
SEED_STRING = """
Press [enter] to start a new game.

    
(Optional) Enter a random seed.
"""
HELP_SHORT =  """(h)elp. (q)uit. deal a (r)ound. reu(s)e discards. (n)ew game. (z)seed.
Control with 🡠 🡢 🡡 🡣, [enter] / [backspace]"""
HELP_1 = """  -- RULES -- 
The goal is to empty the board by taking off three cards at a time from the same column.
You may only take cards from the ends of one column, and they must add up to either 10, 20 or 30 in value. For example, you could try the bottom three cards, or the bottom card and the two top cards etc.
Aces are worth 1, and J, Q, K are worth 10.

"""
HELP_2 = """

  -- KEYBOARD CONTROLS --
[h] \t\tToggle help / keyboard shortcuts
[q] \t\tQuit (without saving)
🡠 🡢 🡡 🡣 \tMove the selector
[enter] \tSelect a card
[backspace] \tUn-select the last card
[s] \t\tMix the discard into the draw pile
[r] \t\tDeal a round of cards
[n] \t\tNew game
[z] \t\tShow the seed

  -- ABOUT --
Minimum recommended window size: 10 x 40.
You can re-play a game by giving the same seed.

Programmed in python with ncurses by Malte Lau Petersen after watching Johanne play this solitaire time and time again.





























 -- Keep scrolling to get more "active" help -- 













  -- CHEAT --
Press [H] to move the cursor to the solution if there is one.
"""

#######################################
# Card class

class Card:
    CARD_TO_VALUE = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5 , "6": 6 , "7": 7,
                     "8": 8, "9": 9 , "10": 10, "J": 10, "Q": 10, "K": 10}
    COLOURS = {'hearts': 1,
               'clubs': 4,
               'spades': 2,
               'diamonds': 3}

    def __init__(self, value, face = 'hearts'):
        _value = str(value)
        if not _value in self.CARD_TO_VALUE.keys():
            logger.critical(f'Invalid card passed to the constructor: {value}')
            raise ValueError(f"Not a valid Card: {_value}")
        
        self.text = _value
        self.value = self.CARD_TO_VALUE[_value]
        self.face = face
        self.color = self.COLOURS[face]

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


def card_color(card):
    return curses.color_pair(card.color)

##########################################
# Typing

Stack = List[Card]
Deck = {
    'cards': Stack,
    'discards': Stack
    }

Game = {
    'deck': Deck,
    'board': List[Stack]
    }

###########################################
# Functions

def new_deck(seed = None) -> Deck:
    # generate a deck of 52 cards
    faces = ['hearts', 'diamonds', 'clubs', 'spades']
    cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    deck = {'cards': [Card(c, face) for c in cards for face in faces],
            'discards': []}
    if seed: random.seed(seed)
    random.shuffle(deck['cards'])
    return deck

def deal_cards(deck: Deck) -> Game:
    # deal 3 cards to 7 stacks to set up the game
    return {
        'board': [[deck['cards'].pop(0) for _ in range(3)] for stack in range(7)],
        'deck': deck
        }

def restack_discard(deck: Deck) -> None:
    # put the discard pile back in the draw pile
    for _ in range(len(deck['discards'])):
        deck['cards'].append(deck['discards'].pop())
    logger.debug("Put discard in to the draw pile")

def deal_round(game: Game, state: int) -> int:
    n_stacks = len(game['board'])
    logger.debug(f"Dealing a round of cards to {n_stacks} columns with state {state}")
    
    for i in range(state, n_stacks):
        try:
            game['board'][i].append(game['deck']['cards'].pop(0))
        except IndexError:
            # no cards left, return the column that failed to get a card
            return i
        
    return 0 # cards dealt, all good

        
def print_game(game: Game, pos: Tuple[int], win) -> None:
    win.addstr(0,0,f"Cards left: {len(game['deck']['cards'])}\tDiscard: {len(game['deck']['discards'])}\n")
    max_depth = 0
    for i in count(): # at row i
        for j, stack in enumerate(game['board']): # column j
            if i >= len(stack): # no cards to print for this stack
                win.addstr("".rjust(3).ljust(4))
            else:
                max_depth = i
                if pos == [j, i]: # the selected card, so add [ ]
                    out = ("[" + stack[i].text + "]").rjust(4).ljust(3)
                    split1 = out.split("[")
                    win.addstr(split1[0] + "[")
                    win.addstr(stack[i].text, card_color(stack[i]))
                    win.addstr("]" + split1[1].split("]")[1])
                else:
                    win.addstr(stack[i].text.rjust(3).ljust(4), card_color(stack[i]))
                    
        if i > max_depth: break # no more cards to add, stop here
        win.addstr("\n")

def card_from_pos(game: Game, pos: List) -> Card:
    # get the card at a given position on the board
    return game['board'][pos[0]][pos[1]]
    
def gen_valid_moves(i: int) -> List[List[int]]:
    # valid moves have to be 3 cards connected to the ends
    # ie first, second, third OR first, second, last, OR ...
    # i = number of cards in the column
    if i < 3: return []
    l = [[a % i,(a+1) % i,(a+2) % i] for a in range(i-3,i+1)]
    [item.sort() for item in l]
    return l

def get_hint(game: Game, hint_state) -> Tuple[List[int], int]:
    for i, stack in enumerate(game['board']):
        for move in gen_valid_moves(len(stack)):
            cards = [card_from_pos(game, (i, m)) for m in move]
            if sum([card.value for card in cards]) in [10,20,30]:
                return [i, move[hint_state]], (hint_state + 1) % 3
    return None, 0


def new_game_get_seed(win):
    # Ask for a random seed to start the game
    

    win.clear()
    win.addstr(0,0, SEED_STRING)


    # create a text box for the user to type in
    editwin = curses.newpad(1,32)
    rectangle(win, 5,0, 1+5+1, 1+32+1)
    
    win_height = curses.LINES-2
    win_width = curses.COLS-4
    win.refresh(0,0,1,2,win_height, win_width)

    box = Textbox(editwin)

    while True:
        # wait for user input
        win.refresh(0,0,1,2,win_height, win_width)
        editwin.refresh(0,0,7,4,7+1, 4+32)
        c = editwin.getch()

        # handle special cases:
        if c == 10: # [enter]
            break
        elif c == curses.KEY_RESIZE: # window resizing
            
            stdscr.clear()
            stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
            stdscr.refresh()
            rectangle(win, 5,0, 1+5+1, 1+32+1)
            
            h, w = stdscr.getmaxyx()
            assert h > 2 and w > 10
            win_height = h - 2
            win_width = w - 4

            win.resize(100, win_width-1)
            win.refresh(0,0,1,2,win_height, win_width)
            
        # draw the user input in the text box
        box.do_command(c)
        
    
    # Get resulting contents
    message = box.gather()
    
    win.clear()
    
    if message:
        logger.info(f"Seed by user: {message}")
        return message
    else:
        seed = random.randint(1, sys.maxsize)
        logger.info(f"Seed generated: {seed}")
        return seed



def main(stdscr) -> Game:

    ####################
    # initialize some variables
    
    pos = [0, 0] # the cursor
    help_state = 0 # 0 = no help, 1 = help screen, 2 = keyboard help only
    proposal = [] # selected cards considered for a match
    round_state = 0 # which column was last dealt to?
    hint_state = 0 # which of the three cards in a hint is shown
    game_lost = False
    game_won = False
    help_pos = 0 # y-position in the help screen
    max_height = 0 # how many rows of cards
    win_height = curses.LINES-2 # how high is the terminal
    win_width = curses.COLS-4 # how wide is the terminal

    #####################
    # set up the window
    
    stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
    stdscr.refresh()

    win = curses.newpad(HELP_LINES + 40, curses.COLS-5)

    # ask user for a seed
    seed = new_game_get_seed(win)
    
    # set up game
    d = new_deck(seed)
    g = deal_cards(d)

    # initial display 
    print_game(g, pos, win)
    max_height = max([len(b) for b in g['board']])
    win.addstr(max_height+2, 0, HELP_SHORT)
    stdscr.refresh()
    win.refresh(0,0,1,2,win_height, win_width)

    #####################
    # game loop
    while True:
        if g['board']: # if there are any columns left
            max_height = max([len(b) for b in g['board']])
        else:
            max_height = 0
            
        stdscr.refresh()

        if help_state == 1: # help screen
            win.refresh(help_pos,0,1,2,win_height, win_width)
        else:
            win.refresh(0,0,1,2,win_height, win_width)
            

        #########################
        # wait for keypress
        c = stdscr.getch()
        win.clear()

        ##################################### q
        if c == ord('q'):
            # quit
            return g
        ##################################### resize        
        elif c == curses.KEY_RESIZE:
            stdscr.clear()
            
            stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
            
            h, w = stdscr.getmaxyx()
            assert h > 2 and w > 10
            win_height = h - 2
            win_width = w - 4

            win.resize(100, win_width-1)
            
        ##################################### h        
        elif c == ord('h'):
            help_state = (help_state + 1) % 3
            if help_state == 0:
                help_pos = 0

        ##################################### ESC                
        elif c == 27:
            # quit help and go back to main game screen
            help_state = 0
            pos = [0,0]

        ##################################### s            
        elif c == ord('s'):
            restack_discard(g['deck'])

        ##################################### r            
        elif c == ord('r'):
            if g['deck']['cards']:
                round_state = deal_round(g, round_state)
                if round_state > 0:
                    # mark with the selector where we got to
                    pos = [round_state-1, len(g['board'][round_state-1])-1]
                else:
                    pos = [0,0]
                max_height = max([len(b) for b in g['board']])
            elif g['deck']['discards']:
                # no cards in draw, but discard still not empty
                pass
            elif not get_hint(g, 0)[1]:
                game_lost = True

        ##################################### H                
        elif c == ord('H'):
            logger.debug("Hint")
            h, hint_state = get_hint(g, hint_state)
            if h:
                pos = h

        ##################################### z                
        elif c == ord('z'):
            # show the seed
            win.addstr(max_height + 4 , 0, f"Seed: {seed}")
                
        ##################################### n
        elif c == ord("n"):
            hint_state = 0
            round_state = 0
            game_lost = False
            game_won = False

            seed = new_game_get_seed(win)
            
            d = new_deck(seed)
            g = deal_cards(d)
            
        ##################################### arrow down                
        elif c == curses.KEY_DOWN:
            if help_state == 1:
                if help_pos < (HELP_LINES + 1):
                    help_pos += 1
            else:
               pos[1] = (pos[1] + 1) % len(g['board'][pos[0]])

        ##################################### arrow up               
        elif c == curses.KEY_UP:
            if help_state == 1:
                if help_pos > 0:
                    help_pos -= 1
            else:
               pos[1] = (pos[1] - 1) % len(g['board'][pos[0]])

        ##################################### arrow right               
        elif c == curses.KEY_RIGHT:
            pos[0] = (pos[0] + 1) % len(g['board'])
            pos[1] = 0
            del proposal[:]

        ##################################### arrow left            
        elif c == curses.KEY_LEFT:
            pos[0] = (pos[0] - 1) % len(g['board'])
            pos[1] = 0
            del proposal[:]

        ##################################### ENTER            
        elif c == 10:
            if len(proposal) <= 2 and not pos in proposal:
                logger.debug(f"Added card to proposal with pos {pos}")
                proposal.append(pos[:])
            if sum([card_from_pos(g, p).value for p in proposal]) in [10,20,30] \
               and len(proposal) == 3:
                proposed_ypos = [p[1] for p in proposal]
                proposed_ypos.sort()
                if proposed_ypos in gen_valid_moves(len(g['board'][pos[0]])):
                    # move is valid, let's go
                    logger.info(f"Move played: {[card_from_pos(g,p) for p in proposal]}")
                    del proposal[:]
                    for i in proposed_ypos[::-1]:
                        # move cards to discard
                        g['deck']['discards'].append(g['board'][pos[0]].pop(i))
                        # check if the column is empty
                        if len(g['board'][pos[0]]) == 0:
                            logger.info(f"Column cleared")
                            del g['board'][pos[0]]

                    # reset some state
                    pos = [0,0]
                    hint_state = 0
                    max_height = max([len(b) for b in g['board']])
                    if not g['board']:
                        game_won = True

        ##################################### BACKSPACE                      
        elif c == curses.KEY_BACKSPACE: 
            if len(proposal) > 0:
                proposal.pop()

        ####################
        # done with keys
        # now update the display
        if help_state == 1:
            win.addstr(0,0, HELP_1)
            COLORS = {'hearts':  curses.color_pair(1),
                      'clubs':  curses.color_pair(4),
                      'spades':  curses.color_pair(2),
                      'diamonds':   curses.color_pair(3)}
            [win.addstr(t + " ",c) for t,c in COLORS.items()]
            win.addstr(HELP_2)
            win.addstr(help_pos + win_height-1, win_width-4, "🡡 🡣")
            
        else:
            # main game screen
            print_game(g, pos, win)
            
            if help_state == 2:
                win.addstr(max_height+3, 0, HELP_SHORT)
            
            if proposal:
                # if there are some selected cards
                win.addstr(max_height + 2, 0, "")
                cards = [card_from_pos(g,p) for p in proposal]
                for c in cards[:-1]:
                    # card1 + card2 + ...
                    win.addstr(c.text, card_color(c))
                    win.addstr(" + ")
                c = cards[-1]
                # ... card3 = sum
                win.addstr(c.text, card_color(c))
                win.addstr(f" = {sum([c.value for c in cards])}")

            if game_lost:
                win.addstr(0, 0, "YOU LOST THE GAME".ljust(curses.COLS-4))
                
            if game_won:
                win.addstr(0, 0, "")
                [win.addstr("YOU won THE GAME".ljust(curses.COLS-4) + "\n") \
                 for _ in range(curses.LINES)]
                
                hint_state = 0
                round_state = 0
                game_lost = False
                game_won = False
                d = new_deck()
                g = deal_cards(d)
                c = win.getch()
                del proposal[:]
                



if __name__ == '__main__':                
    try:
        # set up curses
        stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        curses.curs_set(False)
        
        ######################################
        # Card colours
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        logger.debug("Curses initialized")
        
        g = main(stdscr)
        
    finally:
        curses.nocbreak()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

        logger.info(f"QUIT. Game state: {g}")

        
