import sys
import time
import pygame
import pyphen
import collections

class SpriteInLGroup(pygame.sprite.Sprite):
    def __init__(self, layerd_group: pygame.sprite.AbstractGroup = None, layer: int = 0, groups: list = []):
        """
        :param layerd_group: the layered group for rendering all sprites that this sprite should be added to,
               runtime-evaluated-default value of 'sprites' if that Group exists
        :param layer: the layer the sprite should be in the layered group
        :param groups: list of aux. groups the sprite should be added to
        """
        self.layered_group = globals()["sprites"] if "sprites" in list(globals().keys()) and layerd_group is None\
            else layered_group   # default value that is evaluated at runtime (kind of jank !!)
        try:
            assert self.layered_group is not None
        except AssertionError:
            print("No variable named 'sprites' for the LayeredGroup and no LayeredGroup provided.") # FIXME: still needs to except
        super().__init__()
        self.add_to_groups(self.layered_group, layer, groups)

    def add_to_groups(self, layered_group=None, layer=0, groups=[]):
        if layered_group is not None:
            layered_group.add(self, layer=layer)
        for group in groups:
            group.add(self)


class Player(SpriteInLGroup):
    def __init__(self):
        super().__init__(layer=2) # is now __init__ of custom class
        self.image = pygame.image.load("assets/images/snake_body.png")
        self.rect = self.image.get_rect(topleft=(DISP_X//2, DISP_Y//2))

    def update(self):
        if key_state[pygame.K_SPACE]:  # proof of concept
            self.rect.x -= 1


class Background(SpriteInLGroup):
    def __init__(self, size=(100, 100), bg_color=pygame.Color("white")):
        super().__init__(layer=-1)  # behind everything
        self.bg_color = bg_color
        self.image = pygame.Surface(size)
        self.image.fill(bg_color)
        self.rect = self.image.get_rect(topleft=(0,0))


class Text(SpriteInLGroup):
    def __init__(self, text: str="Missing text", pos=(0,0), font: pygame.font.Font=None,
                 color = (255,255,255), bg_color = (0,0,0), anti_aliased=True, layer=4):
        super().__init__(layer=layer)  # high layer for now
        self.text = text
        self.font: pygame.font.Font = font or pygame.font.SysFont(None, 20)
            # short-hand for: font = font if font is not None else pygame...()
            # needs to be janky runtime-evaluated-default because font isn't init'ed yet
        self.image: pygame.Surface = self.font.render(text, True, (0,0,0))
        self.rect: pygame.rect.Rect = self.image.get_rect(topleft=pos)
        self.color = color
        self.bg_color = bg_color
        self.anti_aliased = anti_aliased


class MultiLineText(SpriteInLGroup):
    max_line_whitespace = 0.2     # should be on a curve, not linear: the smaller width gets, the higher max_... should be, the larger width gets, the smaller max_... should be
    def __init__(self, text: str="Missing text", rect: pygame.Rect=pygame.Rect(0,0,50,50), line_spacing=None, font: pygame.font.Font=None,
                 color = (255,255,255), bg_color = (0,0,0), anti_aliased=True, layer=4, hyphen=None):
        """
        :param text: the text to be displayed in one long possibly multiline string
        :param rect: Rect obj to store top, left, width, height coords of the text box
        :param font: Font obj to store font and font size info
        :param bg_color: background color of whole text box
        :param anti_aliased: True/False
        :param layer: int for the layer in LayeredUpdates
        :param hyphen: the pyphen dic to be used to hyphenate, if left None, then tries to use
        """
        # TODO: single character apearing, rect should it be max size? how should it handle positioning, a text box?,
        #   center alignment (vert & horiz)?, clickable

        super().__init__(layer=layer)
        self.text = text
        self.font: pygame.font.Font = font or pygame.font.SysFont(None, 20)
        self.font_size = self.font.size("")[1]
        self.line_spacing = line_spacing or self.font.get_linesize()//2
        self.image = pygame.Surface((rect.w, rect.h))
        self.image.fill(bg_color)
        self.rect = rect
        self.color = color
        self.bg_color = bg_color
        self.anti_aliased = anti_aliased
        self.hyphen: pyphen.Pyphen = globals()["hyphen"] if "hyphen" in list(globals().keys()) and hyphen is None \
            else hyphen
        try:
            assert self.hyphen is not None
        except AssertionError:
            print("No variable named 'hyphen' for the pyphen dic and no dic provided.")  # FIXME: still needs to except, doesn't produce nice error

        curr_line = []  # list of words in the current line

        # fill line_imgs
        words = collections.deque(self.text.strip().split(" "))
        line_imgs = self.render_words(words)

        # build blit_sequence and blit it to the image
        blit_sequence = []
        for idx, render_line in enumerate(line_imgs):
            if idx * (self.line_spacing + self.font_size) + self.font_size > self.rect.height:
                print("overfull multilinetext in y direction")  # TODO: work in progress
                break
            blit_sequence += [(render_line, pygame.Rect(0, idx * (self.line_spacing + self.font_size), 0, 0))]
        self.image.blits(blit_sequence)


    #auxiliary methods
    def render_words(self, words):
        render_line = lambda line: self.font.render(line, self.anti_aliased, self.color, self.bg_color)  # just a alias
        line_imgs = []  # list of surfaces that each have a line of text rendered onto
        curr_line = []

        while len(words) > 0:
            word = words.popleft()                              # take the newest word
            try:
                i = word.index("\n")                            # look for newline chars
                words.extendleft([word[:i], word[(i + 2):]])    # if found, re-add the words seperately to the queue
            except ValueError:                                  # no newline char found
                if self.too_long(" ".join(curr_line + [word])): # line is too long with extra word
                    short = True if self.too_short(" ".join(curr_line)) else False     # and too short without
                    line_to_render, left_overs = self.get_max_line(([] if short else curr_line) + [word], rest=curr_line if short else [])
                    # spits out maximum lenght of line, and the leftover words for the next line
                    line_imgs += [render_line(line_to_render)]  # render line, add to the list
                    words.extendleft(left_overs)                # save leftovers
                    curr_line = []                              # start new line
                else:
                    curr_line += [word]                         # line not long enough yet, add the word
        line_imgs += [render_line(" ".join(curr_line))]
        return line_imgs

    def too_long(self, line):
        return self.font.size(line)[0] > self.rect.width

    def too_short(self, line):
        return self.font.size(line)[0] < self.rect.width*(1-self.max_line_whitespace)

    def get_max_line(self, line: list, rest=[]) -> (str, list):      # line is a list of words, returns line as string and list of words for next line
        sep, end = " ", ""                                  # concatonate words with space, end with nothing
        if type(line) is str:
            line = [line]                                   # if you mistakenly pass it a single word
        if len(line) == 1:                                  # only one element
            try:
                hyphen_idx = line[0].index("-")             # word already hyphenated, split at hyphenation
            except ValueError:
                line = self.hyphen.inserted(*line).split("-")   # one element, no hyphens
            else:                                           # -> so the list should be of the syllables
                split_word = self.get_max_line([line[0][:hyphen_idx]])
                return split_word[0], [split_word[1][0]+line[0][(hyphen_idx+(1 if split_word[1][0] == "" else 0)):]]
                # split_word[1] is a one-element list within it the rest of the first word as a string,
                # take that and the rest of the word second word (if the first word empty, don't preserve hyphen)
            sep, end = "", "-"                              # concatonate syllables, end with '-'
        i = len(line)
        while self.too_long(" ".join(rest) + sep.join(line[:i]) + end):   # line including end (and possibly rest) is too long
            if i == 0:                                      # reached first item
                if sep == "":                               # case of syllables
                    print(f"syllable '{line[0]}' too long in font size {self.font.size('')} "
                          f"for width of {self.rect.width}, replacing word with '|'")
                    return ("|", "")                        # single syllable is too long, replace with thin char, return
                else:
                    split_word = get_max_line(line[:1])     # single word is too long, split it by recursion
                    return split_word[0], split_word[1] + line[1:]
                    # return the first syllable, and add the rest to the rest of the words
            i -= 1
        return " ".join(rest) + " "*int(bool(rest)) + sep.join(line[:i]) + end, (line[i:] if sep == " " else ["".join(line[i:])])
        # return if there is rest, add that to the front, and if so also extra whitespace, and
        # the first items concatonated to a string, and the last as a list



# initialization
pygame.init()
pygame.font.init()
pygame.mixer.init()
text_language = "de_DE"  # TODO: get from text files
hyphen = pyphen.Pyphen(lang=text_language)

# colors are addressable as strings see https://github.com/pygame/pygame/blob/master/src_py/colordict.py

# init window
DISP_X, DISP_Y = DISPLAY_SIZE = (640, 480)
display: pygame.Surface = pygame.display.set_mode(DISPLAY_SIZE)

# timer
clock = pygame.time.Clock()
FPS = 60

# sprites
sprites = pygame.sprite.LayeredUpdates()

#player = Player()
background = Background(DISPLAY_SIZE)
hyphen_test = MultiLineText("Dampfschifffahrtsgesellschaft, Aufmerksamkeitsdefizit-Hyperaktivitätsstörung,\n Kraftfahrzeug-Haftpflichtversicherung. Depending on the type of background and antialiasing used, this returns different types of Surfaces.\nFor performance reasons, it is good to know what type of image will be used.",
                            rect=pygame.Rect(100,0, 100,480))

mlt2 = MultiLineText(text="Depending on the type of background and antialiasing used, this returns different types of Surfaces.\nFor performance reasons, it is good to know what type of image will be used.",
                     rect=pygame.Rect(300,0,300,300), color=pygame.Color("red"), bg_color=pygame.Color("blue"))

while True:  # Game Loop
    t = time.time()

    # events
    for event in pygame.event.get():
        key_state = pygame.key.get_pressed()
        if event.type == pygame.QUIT or \
                (key_state[pygame.K_LCTRL] or key_state[pygame.K_RCTRL]) and key_state[pygame.K_t]:
            pygame.quit()
            sys.exit()

    # update
    sprites.update()

    # draw sprites
    sprites.draw(display)

    pygame.display.update()
    if t:=time.time()-t > 1/FPS:
        print(f"WARNING: current FPS is {1/t:.4f}")
    clock.tick(FPS)
