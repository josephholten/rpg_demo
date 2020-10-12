from PIL import Image
import numpy as np
import test_game

WHITE = 0
GREY = 180

# create matrix
image_mat = np.array([[WHITE if (((x//test_game.TILE_SIZE) + (y//test_game.TILE_SIZE)) % 2) == 0 else GREY
                 for x in range(test_game.DISP_X)]
                for y in range(test_game.DISP_Y)])

# Creates PIL image
Image.fromarray(np.uint8(image_mat) , 'L').save("assets/background.png")