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
tanks_list: list[gameobjects.Tank] = []

# -- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)

background = pygame.Surface(screen.get_size())

for y in range(current_map.height):
    for x in range(current_map.width):
        background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))

for (x, y, _), image in zip(current_map.start_positions, images.bases):
    base = gameobjects.GameVisibleObject(x, y, image)
    game_objects_list.append(base)

for y in range(current_map.height):
    for x in range(current_map.width):
        box_type: gameobjects.Box = current_map.boxAt(x, y)
        if box_type != 0:
            box = gameobjects.get_box_with_type(x, y, box_type, space)
            game_objects_list.append(box)

for (x, y, orientation), image in zip(current_map.start_positions, images.tanks):
    tank = gameobjects.Tank(x, y, orientation, image, space)
    tanks_list.append(tank)
    game_objects_list.append(tank)

flag = gameobjects.Flag(*current_map.flag_position)
game_objects_list.append(flag)

# ----- Main Loop -----#

# -- Control whether the game run
running = True

skip_update = 0
stop_moving_timer = 0
stop_turning_timer = 0

while running:
    # -- Handle the events
    for event in pygame.event.get():
        # Check if we receive a QUIT event (for instance, if the user press the
        # close button of the window) or if the user press the escape key.
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
        if event.type == KEYDOWN:
            if event.key == K_UP:
                tanks_list[0].accelerate()
                stop_moving_timer = 0.2
            elif event.key == K_DOWN:
                tanks_list[0].decelerate()
                stop_moving_timer = 0.2
            elif event.key == K_LEFT:
                tanks_list[0].turn_left()
                stop_turning_timer = 0.2
            elif event.key == K_RIGHT:
                tanks_list[0].turn_right()
                stop_turning_timer = 0.2
        if event.type == KEYUP:
            if event.key == K_UP or event.key == K_DOWN:
                tanks_list[0].stop_moving()
            if event.key == K_LEFT or event.key == K_RIGHT:
                tanks_list[0].stop_turning()
    
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

    for object in game_objects_list:
        object.update_screen(screen)

    for tank in tanks_list:
        tank.try_grab_flag(flag)
        if tank.has_won():
            running = False

    #   Redisplay the entire screen (see double buffer technique)
    pygame.display.flip()

    #   Control the game framerate
    clock.tick(FRAMERATE)
