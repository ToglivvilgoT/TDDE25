""" Main file for the game.
"""
import pygame
from pygame.locals import *
from pygame.color import *
import pymunk

# ----- Initialisation ----- #

# -- Initialise the display
pygame.init()
pygame.display.set_mode()

# -- Initialise the clock
clock = pygame.time.Clock()

# -- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0, 0.0)
space.damping = 0.1  # Adds friction to the ground for all objects

# -- Import from the ctf framework
# The framework needs to be imported after initialisation of pygame
import ai
import images
import gameobjects
import maps

# -- Constants
FRAMERATE = 50

# -- Variables
#   Define the current level
current_map = maps.map0
#   List of all game objects
game_objects_list = []
tanks_list = []

# -- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)

background = pygame.Surface(screen.get_size())

for y in range(current_map.height):
    for x in range(current_map.width):
        background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))

# <INSERT CREATE BOXES>

# <INSERT CREATE TANKS>

# <INSERT CREATE FLAG>

# ----- Main Loop -----#

# -- Control whether the game run
running = True

skip_update = 0

while running:
    # -- Handle the events
    for event in pygame.event.get():
        # Check if we receive a QUIT event (for instance, if the user press the
        # close button of the window) or if the user press the escape key.
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
    # -- Update physics
    if skip_update == 0:
        # Loop over all the game objects and update their speed in function of their
        # acceleration.
        for obj in game_objects_list:
            obj.update()
        skip_update = 2
    else:
        skip_update -= 1

    #   Check collisions and update the objects position
    space.step(1 / FRAMERATE)

    #   Update object that depends on an other object position (for instance a flag)
    for obj in game_objects_list:
        obj.post_update()

    # -- Update Display

    screen.blit(background, (0, 0))

    # <INSERT DISPLAY OBJECTS>

    #   Redisplay the entire screen (see double buffer technique)
    pygame.display.flip()

    #   Control the game framerate
    clock.tick(FRAMERATE)
