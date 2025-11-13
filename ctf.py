""" Main file for the game.
"""
import pygame
from pygame.locals import *
from pygame.color import *
from pygame import Surface
from pymunk import Space

pygame.init()
pygame.display.set_mode()

import maps
import game_setup
from gameobjects import Tank, GameObject, Flag
from ai import Ai


def handle_key_down_event(event: pygame.event.Event, player: Tank, space: Space, game_objects: list[GameObject]):
    if event.key == K_UP:
        player.accelerate()
    elif event.key == K_DOWN:
        player.decelerate()
    elif event.key == K_LEFT:
        player.turn_left()
    elif event.key == K_RIGHT:
        player.turn_right()
    elif event.key == K_SPACE:
        bullet = player.shoot(space)
        if bullet is not None:
            game_objects.append(bullet)


def handle_key_up_event(event: pygame.event.Event, player: Tank):
    if event.key == K_UP or event.key == K_DOWN:
        player.stop_moving()
    if event.key == K_LEFT or event.key == K_RIGHT:
        player.stop_turning()


def reset_game(tanks: list[Tank], flag: Flag):
    for tank in tanks:
        tank.respawn()
    flag.respawn()


def print_score(scores: dict[Tank, int]):
    for i, score in enumerate(scores.values()):
        print(f'Player {i + 1}: {score}')


def update(
        game_objects: list[GameObject],
        space: Space,
        tanks: list[Tank],
        flag: Flag,
        ais: list[Ai],
        do_update: bool,
        dt: float,
        update_dt: float,
        scores: dict[Tank, int],
        ):
    """ Runs one iteration of the update loop for the game.
        Returns True if game should quit, false other wise.
    """
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            return True
        if event.type == KEYDOWN:
            handle_key_down_event(event, tanks[0], space, game_objects)

        if event.type == KEYUP:
            handle_key_up_event(event, tanks[0])

    for ai in ais:
        ai.decide()

    if do_update:
        for obj in game_objects:
            obj.update(update_dt)

    space.step(dt)

    for obj in game_objects:
        obj.post_update(dt)

    for tank in tanks:
        tank.try_grab_flag(flag)
        if tank.has_won():
            scores[tank] += 1
            print_score(scores)
            reset_game(tanks, flag)

    return False


def draw(screen: Surface, background: Surface, game_objects: list[GameObject]):
    screen.blit(background, (0, 0))

    for object in game_objects:
        object.update_screen(screen)

    pygame.display.flip()


def main():
    FRAMERATE = 50
    PLAYER_AMOUNT = 1

    # variables
    running = True
    skip_update = 0
    update_dt = 0
    clock = pygame.time.Clock()
    current_map = maps.map0

    # setup
    screen = pygame.display.set_mode(current_map.rect().size)

    space = game_setup.space_set_up()
    game_objects, tanks, flag, ais = game_setup.create_game_objects(current_map, space, PLAYER_AMOUNT)
    scores = {tank: 0 for tank in tanks}
    background = game_setup.get_background(current_map.rect().size)

    game_setup.add_collision_handlers(game_objects, space)
    game_setup.create_borders(current_map.width, current_map.height, space)

    while running:
        dt = clock.tick(FRAMERATE) / 1000
        update_dt += dt

        should_quit = update(game_objects, space, tanks, flag, ais, skip_update <= 0, dt, update_dt, scores)
        if should_quit:
            running = False

        if skip_update <= 0:
            skip_update = 2
            update_dt = 0
        else:
            skip_update -= 1

        draw(screen, background, game_objects)


if __name__ == '__main__':
    main()
