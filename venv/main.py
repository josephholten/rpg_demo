import sys
import time
import pygame


class SpriteInLGroup(pygame.sprite.Sprite):
    def __init__(self, layerd_group: pygame.sprite.AbstractGroup = None, layer: int = 0, groups: list = []):
        """
        :param layerd_group: the layered group for rendering all sprites that this sprite should be added to,
               runtime-evaluated-default value of 'sprites' if that Group exists
        :param layer: the layer the sprite should be in the layered group
        :param groups: list of aux. groups the sprite should be added to
        """
        layerd_group = globals()["sprites"] if "sprites" in list(globals().keys()) and layerd_group is None\
            else layerd_group   # default value that is evaluated at runtime (kind of jank !!)
        super().__init__()
        self.add_to_groups(layerd_group, layer, groups)

    def add_to_groups(self, layered_group=None, layer=0, groups=[]):
        if layered_group is not None:
            layered_group.add(self, layer=layer)
        for group in groups:
            group.add(self)


class Player(SpriteInLGroup):
    def __init__(self):
        super().__init__(layer=2) # is now __init__ of custom class
        self.image = pygame.image.load("assets/snake_body.png")
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
    def __init__(self, text: str="Missing text", rect: pygame.Rect=pygame.Rect(0,0,50,50), line_spacing=None, font: pygame.font.Font=None,
                 color = (255,255,255), bg_color = (0,0,0), anti_aliased=True, layer=4):
        """
        :param text: the text to be displayed in one long possibly multiline string
        :param rect: Rect obj to store top, left, width, height coords of the text box
        :param font: Font obj to store font and font size info
        :param bg_color: background color of whole text box
        :param anti_aliased: True/False
        :param layer: int for the layer in LayeredUpdates
        """
        # TODO: how to handle new lines?, word splitting, single character apearing
        # right now: newlines just start a new line

        super().__init__(layer=layer)
        self.text = text
        self.font: pygame.font.Font = font or pygame.font.SysFont(None, 20)
        self.line_spacing = line_spacing or self.font.get_linesize()//2
        self.max_font_height = self.font.get_ascent()+self.font.get_descent()
        #print(self.max_font_height)
        self.image = pygame.Surface((rect.w, rect.h))
        self.image.fill(bg_color)
        self.rect = rect
        self.color = color
        self.bg_color = bg_color
        self.anti_aliased = anti_aliased

        blocks = [line.strip().split(" ") for line in text.strip().splitlines()]  # "a b\nc" --> [['a','b'],['c']]
        curr_line = [];
        line_imgs = []

        # TODO: could be neater
        line_img = lambda line: self.font.render(" ".join(curr_line), self.anti_aliased, self.color, self.bg_color)
        for words in blocks:  # words = one block
            for word in words:
                if self.font.size(word)[0] > self.rect.width:
                    print(f"word too large for width: {word}. replaced with '|'")
                    word = "|"
                if self.font.size(" ".join(curr_line + [word]))[0] > self.rect.width:
                    line_imgs += [line_img(" ".join(curr_line))]  # max size reached
                    curr_line = [word]
                else:
                    curr_line += [word]
            line_imgs += [line_img(" ".join(curr_line))]  # \n --> new line
            curr_line = []

        blit_sequence = []
        for idx, line_img in enumerate(line_imgs):
            if idx * (self.line_spacing + self.font.size("")[1]) > self.rect.height:
                print("overfull in y direction")  # TODO: work in progress
                break
            blit_sequence += [(line_img, pygame.Rect(0, idx * (self.line_spacing + self.font.size("")[1]), 0, 0))]
        self.image.blits(blit_sequence)


# initialization
pygame.init()
pygame.font.init()
pygame.mixer.init()

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
#text = Text()
mlt = MultiLineText(text="Depending on the type of background and antialiasing used, this returns different types of Surfaces. For performance reasons, it is good to know what type of image will be used.", rect=pygame.Rect(0,0,300,300))
mlt2 = MultiLineText(text="Depending on the type of background and antialiasing used, this returns different types of Surfaces.\nFor performance reasons, it is good to know what type of image will be used.", rect=pygame.Rect(300,0,300,300), color=pygame.Color("red"), bg_color=pygame.Color("blue"))


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

