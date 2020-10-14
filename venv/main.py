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
        except AssertionError as err:
            print() # FIXME: still needs to except
            raise NameError("No variable named 'sprites' for the LayeredGroup and no LayeredGroup provided.") from err
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
    def __init__(self, text: str="Missing text", rect: pygame.Rect=pygame.Rect(0,0,50,50), font: pygame.font.Font=None,
                 line_spacing=None, alignment="center", color = (255,255,255), bg_color = (0,0,0), anti_aliased=True, layer=4, hyphen=None, warning=True):
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
        #       alignment vert?, clickable

        super().__init__(layer=layer)
        self.text = text
        self.line_images = []
        self.current_line_number = 0
        self.font: pygame.font.Font = font or pygame.font.SysFont(None, 20)
        self.font_size = self.font.size("")[1]
        self.line_spacing = line_spacing or self.font.get_linesize()//2
        self.possible_alignments = ["left", "center", "right"]
        if alignment not in self.possible_alignments:
            raise ValueError((f"not recognised alignment '{alignment}', possible aligments are: " + "{}, "*len(possible_alignments)).format(*possible_alignments))
        self.alignment = alignment
        self.color = color
        self.bg_color = bg_color

        self.anti_aliased = anti_aliased
        self.hyphen: pyphen.Pyphen = globals()["hyphen"] if "hyphen" in list(globals().keys()) and hyphen is None \
            else hyphen
        try:
            assert self.hyphen is not None
        except AssertionError as err:
            raise NameError("no variable named 'hyphen' for the pyphen dic and no dic provided") from err

        self.image = pygame.Surface((rect.w, rect.h))
        self.image.fill(bg_color)
        self.rect = rect

        # fill line_imgs
        self.line_imgs = self.render_words(self.text.strip().split(" "))


        # calculate max number of lines that can be displayed at once
        self.max_num_lines = 0                  # FIXME: isn't necessarily constant with constant font size
        height = self.rect.height
        if height > self.font_size:
            height -= self.font_size
            self.max_num_lines = 1
        self.max_num_lines += height // (self.font_size + self.line_spacing)

        if warning and self.max_num_lines < len(self.line_imgs):    # warning can be disables manually or by the child class
            print("overfull multilinetext in y direction")

        self.draw_lines_to_screen(self.get_next_lines())

    def get_next_lines(self, reverse=False):
        # in the base class is only called once
        # in the child class on each update
        return self.line_imgs[self.current_line_number-self.max_num_lines*(1 if reverse else 0):
                              self.current_line_number+self.max_num_lines*(0 if reverse else 1)]

    def draw_lines_to_screen(self, lines):
        # build blit_sequence and blit it to the image
        blit_sequence = []
        get_x = lambda rendered_line: 0  # this is left, if somehow alignment isn't one of the keywords raises error
        if self.alignment not in self.possible_alignments:
            raise ValueError((f"not recognised alignment '{alignment}', possible aligments are: " + "{}, "*len(possible_alignments)).format(*possible_alignments))
        if self.alignment == "center":
            get_x = lambda rendered_line: round((self.rect.w - rendered_line.get_rect().w) / 2)
        if self.alignment == "right":
            get_x = lambda rendered_line: self.rect.w - rendered_line.get_rect().w

        for idx, rendered_line in enumerate(lines):
            x = get_x(rendered_line)
            y = idx * (self.line_spacing + self.font_size)
            blit_sequence += [(rendered_line, pygame.Rect(x,y, 0,0))]
        self.image.blits(blit_sequence)

    def update(self):
        pass

    # TODO: textbox that shrinks borders to min, textbox that is clickable and gets new lines

    #auxiliary methods
    def too_long(self, line):
        return self.font.size(line)[0] > self.rect.width

    def too_short(self, line):
        return self.font.size(line)[0] < self.rect.width*(1-self.max_line_whitespace) # TODO: line_whitespace on a curve

    def render_words(self, words: list):
        if type(words) != collections.deque:
            words = collections.deque(words)
        render_line = lambda line: self.font.render(line, self.anti_aliased, self.color, self.bg_color)  # just a alias
        line_imgs = []  # list of surfaces that each have a line of text rendered onto
        curr_line = []

        while len(words) > 0:
            word = words.popleft()                              # take the newest word
            if word == "":
                continue
            if "\n" == word:
                line_imgs += [render_line(" ".join(curr_line))]
                curr_line = []
            elif "\n" in word:
                i = word.index("\n")                            # look for newline chars
                words.extendleft(reversed([word[:i], word[i:(i+1)], word[(i+1):]]))            # if found, re-add the words seperately to the queue
            else:                                               # no newline char found
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

    def get_max_line(self, to_be_split: list, rest=[]) -> (str, list):      # to_be_split is possibly a list of words, returns to_be_split+rest as string and list of words for next to_be_split
        sep, end = " ", ""                                  # concatonate words with space, end with nothing
        if type(to_be_split) is str:
            to_be_split = [to_be_split]                                   # if you mistakenly pass it a single word
        if len(to_be_split) == 1:                                  # only one element
            if "-" in to_be_split[0]:
                hyphen_idx = to_be_split[0].index("-")             # word already hyphenated, split at hyphenation
                split_word = self.get_max_line([to_be_split[0][:hyphen_idx]], rest)# -> so the list should be of the syllables
                return split_word[0], [split_word[1][0] + to_be_split[0][(hyphen_idx + (1 if split_word[1][0] == "" else 0)):]]
                # split_word[1] is a one-element list within it the rest of the first word as a string,
                # take that and the rest of the word second word (if the first word empty, don't preserve hyphen)
            else:
                to_be_split = self.hyphen.inserted(*to_be_split).split("-")# one element, no hyphens
            sep, end = "", "-"                              # concatonate syllables, end with '-'
        i = len(to_be_split)
        while self.too_long(" ".join(rest) + " "*bool(rest) + sep.join(to_be_split[:i]) + end*bool(to_be_split[:i])):   # to_be_split including end (and possibly rest) is too long
            if i == 0:                                      # reached first item
                if sep == "":                               # case of syllables
                    print(f"syllable '{to_be_split[0]}' too long in font size {self.font.size('')[1]} "
                          f"for width of {self.rect.width}")
                    raise ValueError("too small Rect")
                else:
                    split_word = get_max_line(to_be_split[:1])     # single word is too long, split it by recursion
                    return split_word[0], split_word[1] + to_be_split[1:]
                    # return the first syllable, and add the rest to the rest of the words
            i -= 1
        return " ".join(rest) + " "*bool(rest) + sep.join(to_be_split[:i]) + end*bool(to_be_split[:i]), (to_be_split[i:] if sep == " " else ["".join(to_be_split[i:])])
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
hyphen_test = MultiLineText("Dampfschifffahrtsgesellschaft, Aufmerksamkeitsdefizit-Hyperaktivitätsstörung,\n ",#Kraftfahrzeug-Haftpflichtversicherung. Depending on the type of background and antialiasing used, this returns different types of Surfaces.\nFor performance reasons, it is good to know what type of image will be used.",
                            rect=pygame.Rect(100,0, 100,480))

#mlt2 = MultiLineText(text="Depending on the type of background and antialiasing used, this returns different types of Surfaces.\nFor performance reasons, it is good to know what type of image will be used.",
#                     rect=pygame.Rect(300,0,300,300), color=pygame.Color("red"), bg_color=pygame.Color("blue"))
#test = MultiLineText(text="Hello World", rect=pygame.Rect(0,0,5,5))

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
