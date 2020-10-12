import pygame as pg
from pygame.locals import *
import sys
import time

# gimp: RGBA pictures to make parts see through (alpha channel)
# Wo ist die Maus, Wo klickt die Maus -> evets: MouseMotion, MouseButtonUp, MouseButtonDown
# sprites verschwinden lassen -> sprites(liste).remove
# sounds spielen -> siehe unten

pg.init()
pg.font.init()

# fonts
font = pg.font.SysFont("arial", 40)

# colors
WHITE = pg.Color(255, 255, 255)
BLACK = pg.Color(0, 0, 0)

# init window
DISPLAY_SIZE = (512, 512)
display = pg.display.set_mode(DISPLAY_SIZE)

# timer
clock = pg.time.Clock()
FPS = 60


class Player(pg.sprite.Sprite):  # für jede sprite art eine eigene klasse
    def __init__(self):
        super().__init__()
        self.image = pg.image.load("assets/snake_head.png")
        self.surf = pg.Surface((32, 32))
        self.rect = self.surf.get_rect(topleft=(32, 32))

        self._layer = 2  # higher number -> later written -> in front
        sprites.add(self)  # macht es in die sprite gruppe rein

    def update(self):
        if key_state[K_SPACE]:
            self.rect.x -= 1

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Text(pg.sprite.Sprite):  # für jede sprite art eine eigene klasse
    def __init__(self, string="Spiel"):
        super().__init__()
        self.string = string
        self.image = font.render(self.string, True, BLACK)
        self.surf = pg.Surface(font.size(self.string))
        self.rect = self.surf.get_rect(topleft=(64, 64))

        self._layer = 2  # higher number -> later written -> in front
        sprites.add(self)  # macht es in die sprite gruppe rein

    def update(self):
        pass

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# init sprites
sprites = pg.sprite.LayeredUpdates()

player = Player()
text = Text("Spiel")

# music
sound1 = pg.mixer.Sound("assets/neoliberal.ogg")
sound2 = pg.mixer.Sound("assets/Arrival 2016 - Opening & Ending Soundtrack.ogg")
pg.mixer.init()
new_channel = pg.mixer.find_channel()
new_channel.queue(sound1)
time.sleep(3)
new_channel.pause()
time.sleep(1)
sound1.play()
time.sleep(4)
sound1.stop()
channel = pg.mixer.find_channel()
channel.queue(sound2)
# channel.play(sound2)
# pg.mixer.music.load("assets/neoliberal.mp3")
# pg.mixer.music.play()

while True:  # Game Loop
    t = time.time()

    # stuff
    # events
    for event in pg.event.get():
        key_state = pg.key.get_pressed()
        if event.type == QUIT or \
                (key_state[K_LCTRL] or key_state[K_RCTRL]) and key_state[K_w]:
            pg.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_u:
                print("z")
                sprites.remove(text)
    # update
    sprites.update()

    # draw
    pg.draw.rect(display, WHITE, pg.Rect(0, 0, 512, 512))

    sprites.draw(display)

    pg.display.update()

    t = time.time() - t
    if t > 1 / 60:
        print("Time Delay:", t)
    clock.tick(FPS)
