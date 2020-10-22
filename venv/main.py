import sys
import time
import pygame
import pyphen
import collections
import random
import yaml


class SpriteInLGroup(pygame.sprite.Sprite):
    def __init__(self, layered_group: pygame.sprite.AbstractGroup = None, layer: int = 0, groups=None):
        """
        :param layered_group: the layered group for rendering all rendered_sprites that this sprite should be added to,
               runtime-evaluated-default value of 'rendered_sprites' if that Group exists
        :param layer: the layer the sprite should be in the layered group
        :param groups: list of aux. groups the sprite should be added to
        """
        if groups is None:
            groups = []
        self.layer = layer
        self.layered_group = globals()["rendered_sprites"] if "rendered_sprites" in list(
            globals().keys()) and layered_group is None \
            else layered_group  # default value that is evaluated at runtime (kind of jank !! --> not really any more)
        try:
            assert self.layered_group is not None
        except AssertionError as err:
            raise NameError(
                "No variable named 'rendered_sprites' for the LayeredGroup and no LayeredGroup provided.") from err
        super().__init__()
        self.add_to_groups(self.layered_group, layer, groups)

    def add_to_groups(self, layered_group=None, layer=0, groups=None):
        if groups is None:
            groups = []
        if layered_group is not None:
            layered_group.add(self, layer=layer)
        for group in groups:
            group.add(self)

    def on_click(self, mouse):
        pass


class Player(SpriteInLGroup):
    def __init__(self, groups=None):
        if groups is None:
            groups = []
        self.layer = 2
        super().__init__(layer=2, groups=groups)  # is now __init__ of custom class
        self.image = pygame.image.load("assets/images/snake_body.png")
        self.rect = self.image.get_rect(topleft=(DISP_X // 2, DISP_Y // 2))

    def update(self):
        if key_state[pygame.K_SPACE]:  # proof of concept
            self.rect.x -= 1

    def on_click(self, mouse):
        self.rect = pygame.Rect(random.randint(0, DISP_X - self.rect.w), random.randint(0, DISP_Y - self.rect.h),
                                self.rect.w, self.rect.height)


class Background(SpriteInLGroup):
    def __init__(self, size=(100, 100), bg_color=pygame.Color("white")):
        self.layer = -1
        super().__init__(layer=-1)  # behind everything
        self.bg_color = bg_color
        self.image = pygame.Surface(size)
        self.image.fill(bg_color)
        self.rect = self.image.get_rect(topleft=(0, 0))


class TextSettings:
    """
    Wrapper-class for settings relating to text
    """

    def __init__(self, font: pygame.font.Font = None, line_spacing=None, alignment="center",
                 color=(255, 255, 255), bg_color=(0, 0, 0), anti_aliased=True, hyphen=None):
        # FIXME: fill me out
        """
        :param font:
        :param line_spacing:
        :param alignment:
        :param color:
        :param bg_color:
        :param anti_aliased:
        :param hyphen:
        """
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = font or pygame.font.SysFont(None, 20)
        self.font_size = self.font.size("")[1]
        self.line_spacing = line_spacing or self.font.get_linesize() // 2
        self.possible_alignments = ["left", "center", "right"]
        if alignment not in self.possible_alignments:
            raise ValueError((f"not recognised alignment '{alignment}', possible aligments are: " + "{}, " * len(
                self.possible_alignments)).format(*self.possible_alignments))
        self.alignment = alignment

        self.color = color
        self.bg_color = bg_color

        self.anti_aliased = anti_aliased
        self.hyphen = hyphen


class Text(SpriteInLGroup):
    """
    Basic class for rendering text in a box
    """

    def __init__(self, text: str = "Missing text", rect: pygame.Rect = pygame.Rect(0, 0, 50, 50),
                 text_settings: TextSettings = TextSettings(), layer=4, groups=None):
        if groups is None:
            groups = []
        self.layer = layer
        super().__init__(layer=layer, groups=groups)  # high layer for now
        self.text = text
        self.text_settings = text_settings
        self.image: pygame.Surface = self.text_settings.font.render(
            text, text_settings.anti_aliased, text_settings.color, background=text_settings.bg_color)
        self.rect: pygame.rect.Rect = rect


class MultiLineText(SpriteInLGroup):
    """
    Class handling multiple line text
    """

    max_line_whitespace = 0.2  # should be on a curve,

    # not linear: the smaller width gets, the higher max_... should be,
    # the larger width gets, the smaller max_... should be

    def __init__(self, text: str = "Missing text", rect: pygame.Rect = pygame.Rect(0, 0, 50, 50),
                 text_settings: TextSettings = TextSettings(), layer=4, groups=None, warning=True):
        """
        :param text: the text to be displayed in one long possibly multiline string
        :param rect: Rect obj to store top, left, width, height coords of the text box
        :param layer: int for the layer in LayeredUpdates
        """
        # TODO: textbox that shrinks borders to min, textbox that is clickable and gets new lines,
        #  single character apearing, how should it handle positioning, a text box? to wrap the text with borders
        #  alignment vert?, clickable
        # FIXME: is spawned as a regular sprite and drawn there too because it is a SpriteInLGroup, should be toggleable

        self.layer = layer
        if groups is None:
            groups = []
        super().__init__(layer=layer, groups=groups)
        self.text = text
        self.text_settings = text_settings
        self.line_images = []
        self.current_line_number = 0

        self.image = pygame.Surface((rect.w, rect.h))
        self.image.fill(self.text_settings.bg_color)
        self.rect = rect

        # fill line_images
        self.line_images = self.render_words(self.text.strip().split(" "))

        # calculate max number of lines that can be displayed at once
        self.max_num_lines = 0  # FIXME: isn't necessarily constant with constant font size
        height = self.rect.height
        font_size = self.text_settings.font_size
        if height >= font_size:
            height -= font_size
            self.max_num_lines = 1
        self.max_num_lines += height // (font_size + self.text_settings.line_spacing)

        if warning and self.max_num_lines < len(self.line_images):
            # warning can be disables manually or by the child class
            print("overfull multilinetext in y direction")

        self.draw_lines_to_screen(self.get_next_lines())

    def get_next_lines(self, reverse=False):
        # in the base class is only called once
        # in the child class on each update
        # FIXME: what to do, if current_line_number exceeds total number of lines
        if reverse:
            self.current_line_number -= self.max_num_lines
            lines = self.line_images[self.current_line_number - self.max_num_lines:self.current_line_number]
        else:
            lines = self.line_images[self.current_line_number:self.current_line_number + self.max_num_lines]
            self.current_line_number += self.max_num_lines
        return lines

    def draw_lines_to_screen(self, lines):
        # build blit_sequence and blit it to the image
        blit_sequence = []
        pos_align = self.text_settings.possible_alignments
        align = self.text_settings.alignment
        get_x = lambda rendered_line: 0  # this is left, if somehow alignment isn't one of the keywords raises error
        if align not in pos_align:
            raise ValueError((f"not recognised alignment '{align}', possible aligments are: " +
                              "{}, " * len(pos_align)).format(*pos_align))
        if align == "center":
            get_x = lambda rendered_line: round((self.rect.w - rendered_line.get_rect().w) / 2)
        if align == "right":
            get_x = lambda rendered_line: self.rect.w - rendered_line.get_rect().w

        for idx, rendered_line in enumerate(lines):
            x = get_x(rendered_line)
            y = idx * (self.text_settings.line_spacing + self.text_settings.font_size)
            blit_sequence += [(rendered_line, pygame.Rect(x, y, 0, 0))]
        self.image.blits(blit_sequence)

    def update_text(self, reverse=False):  # alias
        self.draw_lines_to_screen(self.get_next_lines(reverse))

    def update(self):
        pass

    # auxiliary methods
    def too_long(self, line):
        return self.text_settings.font.size(line)[0] > self.rect.width

    def too_short(self, line):
        return self.text_settings.font.size(line)[0] < self.rect.width * (
                1 - self.max_line_whitespace)  # TODO: line_whitespace on a curve, see further up

    def render_words(self, words: list):
        if type(words) != collections.deque:
            words = collections.deque(words)

        def render_line(line):
            return self.text_settings.font.render(line, self.text_settings.anti_aliased,
                                                  self.text_settings.color, self.text_settings.bg_color)  # just a alias

        line_images = []  # list of surfaces that each have a line of text rendered onto
        curr_line = []

        while len(words) > 0:
            word = words.popleft()  # take the newest word
            if word == "":
                continue
            if "\n" == word:
                line_images += [render_line(" ".join(curr_line))]
                curr_line = []
            elif "\n" in word:
                i = word.index("\n")  # look for newline chars
                words.extendleft(reversed(
                    [word[:i], word[i:(i + 1)], word[(i + 1):]]))  # if found, re-add the words separately to the queue
            else:  # no newline char found
                if self.too_long(" ".join(curr_line + [word])):  # line is too long with extra word
                    short = True if self.too_short(" ".join(curr_line)) else False  # and too short without
                    line_to_render, left_overs = self.get_max_line(([] if short else curr_line) + [word],
                                                                   rest=curr_line if short else [])
                    # spits out maximum lenght of line, and the leftover words for the next line
                    line_images += [render_line(line_to_render)]  # render line, add to the list
                    words.extendleft(left_overs)  # save leftovers
                    curr_line = []  # start new line
                else:
                    curr_line += [word]  # line not long enough yet, add the word
        line_images += [render_line(" ".join(curr_line))]
        return line_images

    def get_max_line(self, to_be_split: list, rest=None) -> (str, list):
        # to_be_split is possibly a list of words,
        # returns to_be_split+rest as string and list of words for next to_be_split
        if rest is None:
            rest = []
        sep, end = " ", ""  # concatenate words with space, end with nothing
        if type(to_be_split) is str:
            to_be_split = [to_be_split]  # if you mistakenly pass it a single word
        if len(to_be_split) == 1:  # only one element
            if "-" in to_be_split[0]:
                hyphen_idx = to_be_split[0].index("-")  # word already hyphenated, split at hyphenation
                split_word = self.get_max_line([to_be_split[0][:hyphen_idx]],
                                               rest)  # -> so the list should be of the syllables
                return split_word[0], [
                    split_word[1][0] + to_be_split[0][(hyphen_idx + (1 if split_word[1][0] == "" else 0)):]]
                # split_word[1] is a one-element list within it the rest of the first word as a string,
                # take that and the rest of the word second word (if the first word empty, don't preserve hyphen)
            else:
                to_be_split = self.text_settings.hyphen.inserted(*to_be_split).split("-")  # one element, no hyphens
            sep, end = "", "-"  # concatenate syllables, end with '-'
        i = len(to_be_split)
        while self.too_long(" ".join(rest) + " " * bool(rest) + sep.join(to_be_split[:i]) + end * bool(
                to_be_split[:i])):  # to_be_split including end (and possibly rest) is too long
            if i == 0:  # reached first item
                if sep == "":  # case of syllables
                    print(f"syllable '{to_be_split[0]}' too long in font size {self.text_settings.font_size} "
                          f"for width of {self.rect.width}")
                    raise ValueError("too small Rect")
                else:
                    split_word = self.get_max_line(to_be_split[:1])  # single word is too long, split it by recursion
                    return split_word[0], split_word[1] + to_be_split[1:]
                    # return the first syllable, and add the rest to the rest of the words
            i -= 1
        return " ".join(rest) + " " * bool(rest) + sep.join(to_be_split[:i]) + end * bool(to_be_split[:i]), (
            to_be_split[i:] if sep == " " else ["".join(to_be_split[i:])])
        # return if there is rest, add that to the front, and if so also extra whitespace, and
        # the first items concatenated to a string, and the last as a list


class TextBox(SpriteInLGroup):
    """
    Class to hold a multilinetext obj, have padding
    """

    def __init__(self, text: str = "Missing text", rect: pygame.Rect = None,
                 text_settings: TextSettings = TextSettings(), padding=4, border=3, border_col=pygame.Color("grey"),
                 layer=4, groups=None, warning=False, text_height=None):
        """
        :param text:
        :param rect:
        :param text_settings:
        :param padding:
        :param layer:
        :param groups:
        """
        if groups is None:
            groups = []
        self.layer = layer
        super().__init__(layer=layer, groups=groups)
        self.text = text
        self.text_settings = text_settings
        self.padding = padding
        self.border = border
        self.offset = padding + border
        self.border_col = border_col
        if rect is None:
            rect = pygame.Rect(0, 0, 50 + 2 * self.offset, 50 + 2 * self.offset)
            # to have consistent default values for text box sizes
        if text_height is None:
            text_height = rect.h
        self.text_height = text_height
        self.rect = rect
        self.mlt = MultiLineText(text, rect=pygame.Rect(self.rect.x + self.offset, self.rect.y + self.offset,
                                                        self.rect.w - 2 * self.offset,
                                                        self.text_height - 2 * self.offset),
                                 text_settings=text_settings, warning=warning, layer=self.layer)
        self.image = pygame.Surface((self.rect.w, self.rect.h))
        self.image.fill(self.border_col)  # fill with border
        self.image.fill(self.text_settings.bg_color,
                        pygame.Rect(self.border, self.border, self.rect.w - 2 * self.border,
                                    self.rect.h - 2 * self.border))
        self.image.blit(self.mlt.image, self.mlt.rect)  # blit text onto image
        # --> this area is only able to be overridden by overriding self.mlt.image

    def clear(self):  # FIXME: this is neccessary because the mlt is a rendered sprite
        self.mlt.image.fill(self.text_settings.bg_color)


class TextBoxClick(TextBox):
    def __init__(self, text: str = "Missing text", rect: pygame.Rect = pygame.Rect(0, 0, 50, 50),
                 text_settings: TextSettings = TextSettings(), padding=4, border=3, border_col=pygame.Color("grey"),
                 layer=4, groups=None):
        super().__init__(text, rect, text_settings, padding, border, border_col, layer, groups, warning=False)

    def on_click(self, mouse):
        if mouse.button not in {pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT}:
            return
        reverse = False
        if mouse.button == pygame.BUTTON_RIGHT:
            reverse = True
        self.clear()
        self.mlt.draw_lines_to_screen(self.mlt.get_next_lines(reverse))  # --> changes self.image


class TextBoxButton(TextBox):
    def __init__(self, text: str = "Missing text", button_text: str = "Button",
                 rect: pygame.Rect = pygame.Rect(0, 0, 100, 100),
                 text_settings: TextSettings = TextSettings(),
                 text_settings_button=TextSettings(color=pygame.Color("black"), bg_color=pygame.Color("white")),
                 padding=4, border=3, text_height=70, border_col=pygame.Color("grey"), layer=4, groups=None):
        self.layer = layer
        self.padding = padding
        self.border = border
        self.offset = self.padding + self.border
        self.rect = rect
        self.text_height = text_height
        self.text = text
        self.button_text = button_text
        super().__init__(text, rect, text_settings, padding, border, border_col, layer, groups,
                         text_height=self.text_height)
        print(self.rect.y + self.text_height - 3)
        # FIXME: why the fuck does this look right, something about text_height is fucked argh
        self.button = Button(self, id_str="next", text=self.button_text,
                             rect=pygame.Rect(self.rect.x + self.offset,
                                              self.rect.y + self.text_height - 3,
                                              80, 26), padding=2, border=2, border_col=pygame.Color("red"),
                             text_settings=text_settings_button)

    def on_button(self, id_str, mouse):
        if id_str == "next":
            #print(f"button {id_str} was clicked and is getting new lines")
            self.clear()
            self.mlt.update_text(reverse=True if mouse.button == pygame.BUTTON_RIGHT else False)


class Button(SpriteInLGroup):
    def __init__(self, container=None, id_str="", text: str = "Button", rect: pygame.Rect = None,
                 text_settings: TextSettings = TextSettings(),
                 padding=2, border=2, border_col=pygame.Color("black"), layer=4, groups=None, func=lambda: None):
        self.container: SpriteInLGroup = container
        if type(container) == SpriteInLGroup:
            try:
                assert hasattr(container, "on_button") and callable(getattr(container, "on_button"))
            except AssertionError as err:
                raise TypeError("container needs a 'on_button(id_str, mouse)' function defined") from err
        if groups is None:
            groups = []
        if container is not None:
            self.layer = max(layer, self.container.layer + 1)
        else:
            self.layer = layer
        super().__init__(layer=self.layer, groups=groups)
        self.id_str = id_str  # this is an id that is internal to the container sprite
        self.text: str = text
        self.text_settings: TextSettings = text_settings
        self.padding: int = padding
        self.border: int = border
        self.offset: int = padding + border
        self.border_col: pygame.Color = border_col
        if rect is None:
            rect = pygame.Rect(0, 0, 50 + 2 * self.offset, self.text_settings.font_size + 1 + 2 * self.offset)
        self.rect = rect
        self.textbox = TextBox(self.text, self.rect, self.text_settings, self.padding, self.border, self.border_col,
                               self.layer)
        self.func = func

        self.image = pygame.Surface(self.rect.size)
        self.image.blit(self.textbox.image, self.textbox.rect)

    def on_click(self, mouse):
        if self.container is None:  # containerless button
            self.func()  # then do the provided func
        else:
            self.container.on_button(self.id_str, mouse)  # was type checked in __init__


class Mouse(pygame.sprite.Sprite):
    def __init__(self, pos=(0, 0), button=None):
        super().__init__()
        self.pos = pos
        self.button = button
        self.rect = pygame.Rect(pos, (1, 1))

    def update(self, pos, button):
        if pos is None:  # in case one wants to render the mouse
            pos = self.rect.x, self.rect.y
        if button is None:
            button = self.button
        self.rect.x, self.rect.y = pos
        self.button = button


# initialization
pygame.init()
pygame.font.init()
pygame.mixer.init()
text_language = "de_DE"  # TODO: get from text files/ config files
hyphen = pyphen.Pyphen(lang=text_language)
with open("assets/text/testing_text.yml") as file:
    test_text = yaml.load(file.read())["random_text_with_newline"]  # FIXME: really slow loading
# TODO: loading screen?

# colors are addressable as strings see https://github.com/pygame/pygame/blob/master/src_py/colordict.py

# init window
DISP_X, DISP_Y = DISPLAY_SIZE = (640, 480)
display: pygame.Surface = pygame.display.set_mode(DISPLAY_SIZE)

# timer
clock = pygame.time.Clock()
FPS = 60

# sprites
rendered_sprites = pygame.sprite.LayeredUpdates()
clickable = pygame.sprite.Group()
text_settings = TextSettings(hyphen=hyphen)
text_settings_button = TextSettings(bg_color=pygame.Color("white"), color=pygame.Color("black"), hyphen=hyphen)

mouse = Mouse()
mouse_group = pygame.sprite.GroupSingle(mouse)
player = Player()
background = Background(DISPLAY_SIZE)
text = TextBoxClick(text="hello world my name is textboxclick", text_settings=text_settings,
                    rect=pygame.Rect(200, 0, 100, 100))

buttonbox = TextBoxButton(text=test_text, text_settings=text_settings, text_settings_button=text_settings_button)

while True:  # Game Loop
    t = time.time()

    # handle events
    for event in pygame.event.get():
        key_state = pygame.key.get_pressed()
        if event.type == pygame.QUIT or \
                (key_state[pygame.K_LCTRL] or key_state[pygame.K_RCTRL]) and \
                (key_state[pygame.K_t] or key_state[pygame.K_w]):
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse.update(event.pos, event.button)
            mouse_collisions = pygame.sprite.groupcollide(rendered_sprites, mouse_group, False, False)
            # get only top level sprite
            clicked_sprite: SpriteInLGroup = max(mouse_collisions.keys(), key=rendered_sprites.get_layer_of_sprite)
            clicked_sprite.on_click(mouse)

    # update objects
    rendered_sprites.update()

    # clear screen
    display.fill(pygame.Color("black"))

    # draw rendered_sprites
    rendered_sprites.draw(display)

    # update screen
    pygame.display.update()
    if t := time.time() - t > 1 / FPS:
        print(f"WARNING: current FPS is {1 / t:.4f}")
    clock.tick(FPS)
