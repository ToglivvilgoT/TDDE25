""" Main file for the game.
"""
import pygame
from pygame.locals import *
from pygame.color import *

pygame.init()
pygame.display.set_mode()

from gameobjects import GameObject, Tank
import maps
import game_setup


def main():
    FRAMERATE = 50
    running = True

    skip_update = 0
    update_dt = 0
    clock = pygame.time.Clock()

    current_map = maps.map0
    space = game_setup.space_set_up()
    game_objects, tanks_list, flag = game_setup.create_game_objects(current_map, space)

    screen = pygame.display.set_mode(current_map.rect().size)

    background = game_setup.get_background(current_map.rect().size)

    game_setup.add_collision_handlers(game_objects, space)
    game_setup.create_borders(current_map.width, current_map.height, space)

    while running:
        dt = clock.tick(FRAMERATE) / 1000
        update_dt += dt

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    tanks_list[0].accelerate()
                elif event.key == K_DOWN:
                    tanks_list[0].decelerate()
                elif event.key == K_LEFT:
                    tanks_list[0].turn_left()
                elif event.key == K_RIGHT:
                    tanks_list[0].turn_right()
                elif event.key == K_SPACE:
                    bullet = tanks_list[0].shoot(space)
                    if bullet is not None:
                        game_objects.append(bullet)
                elif event.key == K_KP_ENTER:
                    bullet = tanks_list[1].shoot(space)
                    if bullet is not None:
                        game_objects.append(bullet)

            if event.type == KEYUP:
                if event.key == K_UP or event.key == K_DOWN:
                    tanks_list[0].stop_moving()
                if event.key == K_LEFT or event.key == K_RIGHT:
                    tanks_list[0].stop_turning()

        if skip_update == 0:
            for obj in game_objects:
                obj.update(update_dt)
            update_dt = 0
            skip_update = 2
        else:
            skip_update -= 1

        space.step(dt)

        for obj in game_objects:
            obj.post_update(dt)

        screen.blit(background, (0, 0))

        for object in game_objects:
            object.update_screen(screen)

        for tank in tanks_list:
            tank.try_grab_flag(flag)
            if tank.has_won():
                running = False

        pygame.display.flip()


if __name__ == '__main__':
    main()
