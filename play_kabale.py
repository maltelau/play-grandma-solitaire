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

from typing import NamedTuple, List, Dict, Tuple
from collections import namedtuple

import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from itertools import count
import random
import sys
# import multiprocessing

# import pandas as pd
# import ggplot as gg

# import cProfile
import logging

######################################
# Logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

HELP_LINES = 80

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
        # super().__init__()
        
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

Deck = {
    'cards': List[Card],
    'discards': List[Card]
    }

Stack = List[Card]
Game = {
    'deck': Deck,
    'board': List[Stack]
    }

###########################################
# Functions

def new_deck(seed = None) -> Deck:
    faces = ['hearts', 'diamonds', 'clubs', 'spades']
    cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    deck = {'cards': [Card(c, face) for c in cards for face in faces],
            'discards': []}
    if seed: random.seed(seed)
    random.shuffle(deck['cards'])
    return deck

def deal_cards(deck: Deck) -> Game:
    return {
        'board': [[deck['cards'].pop(0) for _ in range(3)] for stack in range(7)],
        'deck': deck
        }

def restack_discard(deck):
    for _ in range(len(deck['discards'])):
        deck['cards'].append(deck['discards'].pop())

def deal_round(game: Game, state):
    n_stacks = len(game['board'])
    for i in range(state, n_stacks):
        try:
            game['board'][i].append(game['deck']['cards'].pop(0))
        except IndexError:
            return i
    return 0

        
def print_game(game: Game, pos, win) -> None:
    win.addstr(0,0,f"Cards left: {len(game['deck']['cards'])}\tDiscard: {len(game['deck']['discards'])}\n")
    max_depth = 0
    for i in count(): # at row i
        for j, stack in enumerate(game['board']): # column j
            if i >= len(stack): # no cards to print for this stack
                win.addstr("".rjust(3).ljust(4))
            else:
                max_depth = i
                if pos == [j, i]:
                    out = ("[" + stack[i].text + "]").rjust(4).ljust(3)
                    split1 = out.split("[")
                    win.addstr(split1[0] + "[")
                    win.addstr(stack[i].text, card_color(stack[i]))
                    win.addstr("]" + split1[1].split("]")[1])
                else:
                    win.addstr(stack[i].text.rjust(3).ljust(4), card_color(stack[i]))
        if i > max_depth: break
        win.addstr("\n")
    # win.addstr(0,0,out)
    #return out

def card_from_pos(game: Game, pos: List) -> Card:
    return game['board'][pos[0]][pos[1]]
    
def gen_valid_moves(i):
    if i < 3: return []
    l = [[a % i,(a+1) % i,(a+2) % i] for a in range(i-3,i+1)]
    [item.sort() for item in l]
    return l

def get_move_value(move):
    pass

def get_hint(game: Game, hint_state):
    for i, stack in enumerate(game['board']):
        for move in gen_valid_moves(len(stack)):
            cards = [card_from_pos(game, (i, m)) for m in move]
            if sum([card.value for card in cards]) in [10,20,30]:
                return [i, move[hint_state]], (hint_state + 1) % 3
    return None, 0


def new_game_get_seed(win):
    

    win.clear()
    win.addstr(0,0, """
Press [enter] to start a new game.

    
(Optional) Enter a random seed.
""")

    #win.refresh(0,0,1,2,win_height, win_width)
            
    editwin = curses.newpad(1,32)
    # editwin = curses.newwin(1,32, 7,4)
    rectangle(win, 5,0, 1+5+1, 1+32+1)
    win_height = curses.LINES-2
    win_width = curses.COLS-4
    win.refresh(0,0,1,2,win_height, win_width)

    box = Textbox(editwin)
    
    # Let the user edit until Ctrl-G is struck.
    while True:
        win.refresh(0,0,1,2,win_height, win_width)
        editwin.refresh(0,0,7,4,7+1, 4+32)
        c = editwin.getch()
        if c == 10:
            break
        elif c == curses.KEY_RESIZE:
            stdscr.clear()
            
            stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
            stdscr.refresh()
            rectangle(win, 5,0, 1+5+1, 1+32+1)
            
            h, w = stdscr.getmaxyx()
            assert h > 2 and w > 10
            win_height = h - 2
            win_width = w - 4

            #if win_width > 40:
            win.resize(100, win_width-1)
            win.refresh(0,0,1,2,win_height, win_width)
            
            
        box.do_command(c)
        
    #box.edit()
    
    # Get resulting contents
    message = box.gather()
    
    win.clear()
    if message:
        return message
    else:
        return None



def main(stdscr):
    
    ######################################
    # Card colours
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    #g['board'][0].append(Card('K'))
    #g['board'][0].append(Card('K'))
    #g['board'][0].append(Card('K'))

    # initialize some variables
    pos = [0, 0]
    help_state = 0
    proposal = []
    lp = []
    round_state = 0
    hint_state = 0
    game_lost = False
    game_won = False
    help_pos = 0

    stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
    stdscr.refresh()

    win = curses.newpad(100, curses.COLS-5)

    seed = new_game_get_seed(win)
    if not seed:
        seed = random.randint(1, sys.maxsize)
    
    # set up game
    d = new_deck(seed)
    g = deal_cards(d)

    # initial display 
    print_game(g, pos, win)
    max_height = max([len(b) for b in g['board']])
    win.addstr(max_height+2, 0, """(h)elp. (q)uit. deal a (r)ound. reu(s)e discards. (n)ew game. (z)seed.
Control with [arrow keys], [enter] / [back]""")
    stdscr.refresh()
    win_height = curses.LINES-2
    win_width = curses.COLS-4
    win.refresh(0,0,1,2,win_height, win_width)

    # game loop
    while True:
        if g['board']:
            max_height = max([len(b) for b in g['board']])
        else:
            max_height = 0
        stdscr.refresh()

        
        #win.addstr(10,0, " " + str(pos) + " " + str(len(g['board'])))
        #win.addstr(11,0, " " + str(pos) + " " + str(len(g['board'])))
        
        if help_state == 1:
            win.refresh(help_pos,0,1,2,win_height, win_width)
        else:
            win.refresh(0,0,1,2,win_height, win_width)
            

        
        # wait for keypresses
        c = stdscr.getch()
        
        win.clear()

    
    
        
        if c == ord('q'):
            return g
        
        elif c == curses.KEY_RESIZE:
            stdscr.clear()
            #win.clear()
            
            stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
            
            h, w = stdscr.getmaxyx()
            assert h > 2 and w > 10
            win_height = h - 2
            win_width = w - 4

            #if win_width > 40:
            win.resize(100, win_width-1)
            #win.resize(h-2, w-4)
        
        elif c == ord('h'):
            help_state = (help_state + 1) % 3
            if help_state == 0:
                help_pos = 0

        elif c == 27: # ESC
            help_state = 0
            pos = [0,0]
            
        elif c == ord('s'):
            restack_discard(g['deck'])
            
        elif c == ord('r'):
            if g['deck']['cards']:
                round_state = deal_round(g, round_state)
                if round_state > 0:
                    pos = [round_state-1, len(g['board'][round_state-1])-1]
                max_height += 1
            elif g['deck']['discards']:
                pass
            else:
                game_lost = True

        elif c == ord('H'):
            h, hint_state = get_hint(g, hint_state)
            if h:
                pos = h

        elif c == ord('z'):
            win.addstr(max_height + 4 , 0, f"Seed: {seed}")
                

        elif c == ord("n"):
            hint_state = 0
            round_state = 0
            game_lost = False
            game_won = False

            seed = new_game_get_seed(win)
            
            d = new_deck(seed)
            g = deal_cards(d)
            
                
        elif c == curses.KEY_DOWN: # down
            if help_state == 1:
                if help_pos < (HELP_LINES + 1):
                    help_pos += 1
            else:
               pos[1] = (pos[1] + 1) % len(g['board'][pos[0]])
            
        elif c == curses.KEY_UP: # up
            if help_state == 1:
                if help_pos > 0:
                    help_pos -= 1
            else:
               pos[1] = (pos[1] - 1) % len(g['board'][pos[0]])
            
        elif c == curses.KEY_RIGHT: # right
            pos[0] = (pos[0] + 1) % len(g['board'])
            pos[1] = 0
            del proposal[:]
            
        elif c == curses.KEY_LEFT: # left
            pos[0] = (pos[0] - 1) % len(g['board'])
            pos[1] = 0
            del proposal[:]
            
        elif c == 10: # enter
            if len(proposal) <= 2 and not pos in proposal:
                proposal.append(pos[:])
            if sum([card_from_pos(g, p).value for p in proposal]) in [10,20,30] \
               and len(proposal) == 3:
                proposed_ypos = [p[1] for p in proposal]
                proposed_ypos.sort()
                if proposed_ypos in gen_valid_moves(len(g['board'][pos[0]])):
                    # move is valid, let's go
                    lp = proposal[:]
                    del proposal[:]
                    for i in proposed_ypos[::-1]:
                        g['deck']['discards'].append(g['board'][pos[0]].pop(i))
                        if len(g['board'][pos[0]]) == 0:
                            del g['board'][pos[0]]
                    pos = [0,0]
                    hint_state = 0
                    max_height = max([len(b) for b in g['board']])
                    if not g['board']:
                        game_won = True
                    
        elif c == curses.KEY_BACKSPACE: # delete
            if len(proposal) > 0:
                proposal.pop()

        #win.addstr(11,0,str(c) + " " + str(pos) + " " + str(len(g['board'])))

        # now update the display
        if help_state == 1:
            win.addstr(0,0, """  -- RULES -- 
The goal is to empty the board by taking off three cards at a time from the same column.
You may only take cards from the ends of one column, and they must add up to either 10, 20 or 30 in value. For example, you could try the bottom three 
cards, or the bottom card and the two top cards.
Aces are worth 1, and J, Q, K are worth 10.

""")
            
            COLORS = {'hearts':  curses.color_pair(1),
                      'clubs':  curses.color_pair(4),
                      'spades':  curses.color_pair(2),
                      'diamonds':   curses.color_pair(3)}
            [win.addstr(t + " ",c) for t,c in COLORS.items()]
            win.addstr("""

  -- KEYBOARD CONTROLS --
[h] \t\tToggle help / keyboard shortcuts
[q] \t\tQuit (without saving)
[arrow keys] \tMove the selector
[enter] \tSelect a card
[delete] \tUn-select the last card
[s] \t\tMix the discard into the draw pile
[r] \t\tDeal a round of cards
[n] \t\tNew game
[z] \t\tShow the seed

  -- ABOUT --
Minimum recommended window size: 10 x 40.
You can re-play a game by giving the same seed.

Programmed in python with ncurses by Malte Lau Petersen.





























 -- Keep scrolling to get more "active" help -- 













  -- CHEAT --
Press [H] to move the cursor to the solution if there is one.
""")
        else:
            print_game(g, pos, win)
            # win.addstr(0, 0, print_game(g, pos))
            
            if help_state == 2:
                win.addstr(max_height+3, 0, """(h)elp. (q)uit. deal a (r)ound. reu(s)e discards. (n)ew game. (z)seed.
Control with [arrow keys], [enter] / [back]\n""")
                #win.addstr(max_height + 3, 0, "keys = [h, q, s, r, n, z, arrows, enter, delete]\n")
                #[win.addstr(t + " ",c) for t,c in COLORS.items()]
            
            if proposal:
                win.addstr(max_height + 2, 0, "")
                cards = [card_from_pos(g,p) for p in proposal]
                for c in cards[:-1]:
                    win.addstr(c.text, card_color(c))
                    win.addstr(" + ")
                c = cards[-1]
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
                



try:
    # set up curses
    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    curses.curs_set(False)
    g = main(stdscr)
    
finally:
    curses.nocbreak()
    curses.echo()
    stdscr.keypad(False)
    curses.endwin()

    [print(b) for b in g['board']]
    print(g['deck'])
