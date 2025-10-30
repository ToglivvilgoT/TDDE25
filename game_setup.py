from typing import Literal
from pygame import Surface
from pymunk import Space, Arbiter, Body, Segment

import images
from gameobjects import GameObject, GameVisibleObject, Box, Tank, Flag, Bullet, get_box_with_type
from ai import Ai
from maps import Map


def space_set_up() -> Space:
    """Create and return a new pymunk Space."""
    space = Space()
    space.gravity = (0.0, 0.0)
    space.damping = 0.1  # Adds friction to the ground for all objects
    return space


def get_background(size: tuple[int, int]) -> Surface:
    """Create and return a background image with grass texture."""
    background = Surface(size)

    for y in range(size[1]):
        for x in range(size[0]):
            background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))

    return background


def create_bases(positions: list[tuple[float, float, float]]) -> list[GameObject]:
    """Create and return a list of bases."""
    bases = []
    for (x, y, _), image in zip(positions, images.bases):
        base = GameVisibleObject(x, y, image)
        bases.append(base)
    
    return bases


def create_boxes(map: Map, space: Space) -> list[Box]:
    """Create and return a list of boxes."""
    boxes = []
    for y in range(map.height):
        for x in range(map.width):
            box_type: Box = map.boxAt(x, y)
            if box_type != 0:
                box = get_box_with_type(x, y, box_type, space)
                boxes.append(box)

    return boxes


def create_tanks(
        positions: list[tuple[float, float, float]],
        space: Space,
        player_amount: int,
        game_objects: list[GameObject],
        current_map: Map,
        ) -> tuple[list[Tank], list[Ai]]:
    """Creates and returns a list of tanks and AI:s."""
    tanks = []
    ais = []
    for (x, y, orientation), image in zip(positions, images.tanks):
        tank = Tank(x, y, orientation, image, space)
        tanks.append(tank)
        if player_amount <= 0:
            ais.append(Ai(tank, game_objects, tanks, space, current_map))
        else:
            player_amount -= 1

    return tanks, ais


def create_game_objects(map: Map, space: Space, player_amount: int) -> tuple[list[GameObject], list[Tank], Flag, list[Ai]]:
    """Creates all game objects needed for the game."""
    game_objects = create_bases(map.start_positions)
    game_objects.extend(create_boxes(map, space))
    tanks, ais = create_tanks(map.start_positions, space, player_amount, game_objects, map)
    game_objects.extend(tanks)
    flag = Flag(*map.flag_position)
    game_objects.append(flag)
    return game_objects, tanks, flag, ais


def create_borders(width: float, height: float, space: Space):
    """Create the borders of the map."""
    RADIUS = 0.01
    borders = Body(body_type=Body.STATIC)
    top = Segment(borders, (0, 0), (width, 0), RADIUS)
    right = Segment(borders, (width, 0), (width, height), RADIUS)
    bottom = Segment(borders, (0, height), (width, height), RADIUS)
    left = Segment(borders, (0, 0), (0, height), RADIUS)
    space.add(borders, top, right, bottom, left)


def add_bullet_tank_collision_handler(game_objects: list[GameObject], space: Space):
    def collision_handler(arbiter: Arbiter, space: Space, data: dict[Literal['game_objects'], list[GameObject]]):
        bullet, tank = arbiter.shapes
        bullet: Bullet = bullet.parent
        tank: Tank = tank.parent
        tank.respawn()
        bullet.remove(space)
        game_objects = data['game_objects']
        if bullet in game_objects:
            game_objects.remove(bullet)

        return False

    handler = space.add_collision_handler(Bullet.COLLISION_TYPE, Tank.COLLISION_TYPE)
    handler.data['game_objects'] = game_objects
    handler.pre_solve = collision_handler


def add_bullet_wood_box_collision_handler(game_objects: list[GameObject], space: Space):
    def collision_handler(arbiter: Arbiter, space: Space, data: dict[Literal['game_objects'], list[GameObject]]):
        bullet, box = arbiter.shapes
        bullet: Bullet = bullet.parent
        box: Box = box.parent

        game_objects = data['game_objects']

        box.remove(space)
        if box in game_objects:
            game_objects.remove(box)
        bullet.remove(space)
        if bullet in game_objects:
            game_objects.remove(bullet)

        return False

    handler = space.add_collision_handler(Bullet.COLLISION_TYPE, Box.WOOD_BOX_COLLISION_TYPE)
    handler.data['game_objects'] = game_objects
    handler.pre_solve = collision_handler


def add_bullet_other_collision_handler(game_objects: list[GameObject], space: Space):
    def collision_handler(arbiter: Arbiter, space: Space, data: dict[Literal['game_objects'], list[GameObject]]):
        bullet, _ = arbiter.shapes
        bullet: Bullet = bullet.parent
        game_objects = data['game_objects']
        bullet.remove(space)
        if bullet in game_objects:
            game_objects.remove(bullet)

        return False

    handler = space.add_collision_handler(Bullet.COLLISION_TYPE, 0)
    handler.data['game_objects'] = game_objects
    handler.pre_solve = collision_handler


def add_collision_handlers(game_objects: list[GameObject], space: Space):
    add_bullet_tank_collision_handler(game_objects, space)
    add_bullet_wood_box_collision_handler(game_objects, space)
    add_bullet_other_collision_handler(game_objects, space)