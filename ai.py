""" This file contains function and classes for the Artificial Intelligence used in the game.
"""

import math
from collections import defaultdict, deque

import pymunk
from pymunk import Vec2d, Space
import gameobjects
from gameobjects import Tank, GameObject, Box
from maps import Map

# NOTE: use only 'map0' during development!

MIN_ANGLE_DIF = math.radians(3)   # 3 degrees, a bit more than we can turn each tick


def angle_between_vectors(vec1: Vec2d, vec2: Vec2d):
    """ Since Vec2d operates in a cartesian coordinate space we have to
        convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2
    vec = vec.perpendicular()
    return vec.angle


def periodic_difference_of_angles(angle1, angle2):
    """ Compute the difference between two angles.
    """
    return (angle1 % (2 * math.pi)) - (angle2 % (2 * math.pi))


class Ai:
    """ A simple ai that finds the shortest path to the target using
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes. """

    def __init__(self, tank: Tank, game_objects_list: list[GameObject], tanks_list: list[Tank], space: Space, current_map: Map):
        self.tank = tank
        self.game_objects_list = game_objects_list
        self.tanks_list = tanks_list
        self.space = space
        self.current_map = current_map
        self.flag = None
        self.max_x = current_map.width - 1
        self.max_y = current_map.height - 1

        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()

    def update_grid_pos(self):
        """ This should only be called in the beginning, or at the end of a move_cycle. """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)

    def decide(self):
        """ Main decision function that gets called on every tick of the game.
        """
        bullet = self.maybe_shoot()
        if bullet is not None:
            self.game_objects_list.append(bullet)

        next(self.move_cycle)

    def maybe_shoot(self):
        """ Makes a raycast query in front of the tank. If another tank
            or a wooden box is found, then we shoot.
        """
        direction: Vec2d = self.tank.body.rotation_vector.rotated(math.pi / 2)
        start_offset = direction.scale_to_length(0.5)
        end_offset = direction.scale_to_length(self.max_x + self.max_y)
        start = self.tank.body.position + start_offset
        end = self.tank.body.position + end_offset
        hit = self.space.segment_query_first(start, end, 0, pymunk.ShapeFilter())
        if hit is not None and hasattr(hit, 'shape') and hasattr(hit.shape, 'parent'):
            hit_obj = hit.shape.parent
            is_tank = isinstance(hit_obj, Tank)
            is_wood_box = isinstance(hit_obj, Box) and hit.shape.parent.destructible
            if is_tank or is_wood_box:
                return self.tank.shoot(self.space)

    def move_cycle_gen(self):
        """ A generator that iteratively goes through all the required steps
            to move to our goal.
        """
        while True:
            # find path
            path = self.find_shortest_path()
            if not path:
                yield
                continue
            next_coord = path.popleft()

            # turning
            target_vector = Vec2d(*next_coord) - self.grid_pos
            current_angle = target_vector.get_angle_between(self.tank.body.rotation_vector.rotated_degrees(90))
            if current_angle > MIN_ANGLE_DIF:
                self.tank.turn_left()
            elif current_angle < -MIN_ANGLE_DIF:
                self.tank.turn_right()
            while abs(current_angle) > MIN_ANGLE_DIF:
                self.tank.stop_moving()
                yield
                current_angle = target_vector.get_angle_between(self.tank.body.rotation_vector.rotated_degrees(90))
            self.tank.stop_turning()

            # driving
            self.tank.accelerate()
            target_center = next_coord + (0.5, 0.5)
            distance = target_center.get_distance(self.tank.body.position)
            prev_distance = distance + 1
            while distance < prev_distance:
                yield
                prev_distance = distance
                distance = target_center.get_distance(self.tank.body.position)
            self.update_grid_pos()

    def find_shortest_path(self):
        """ A simple Breadth First Search using integer coordinates as our nodes.
            Edges are calculated as we go, using an external function.
        """
        paths: dict[Vec2d, list[Vec2d]] = {self.grid_pos: []}
        que = deque((self.grid_pos,))
        visited = {self.grid_pos}
        target = self.get_target_tile()
        while que:
            current = que.popleft()
            if current == target:
                return deque(paths[current])
            for neighbor in self.get_tile_neighbors(current):
                if neighbor not in visited:
                    que.append(neighbor)
                    visited.add(neighbor)
                    paths[neighbor] = paths[current] + [neighbor]
        return deque()

    def get_target_tile(self):
        """ Returns position of the flag if we don't have it. If we do have the flag,
            return the position of our home base.
        """
        if self.tank.flag is not None:
            x, y = self.tank.start_position
        else:
            self.get_flag()  # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """ This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """
        if self.flag is None:
            # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        return self.flag

    def get_tile_of_position(self, position_vector):
        """ Converts and returns the float position of our tank to an integer position. """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec: Vec2d):
        """ Returns all bordering grid squares of the input coordinate.
            A bordering square is only considered accessible if it is grass
            or a wooden box.
        """
        neighbors = (coord_vec + offset for offset in ((1, 0), (0, 1), (-1, 0), (0, -1)))  # Find the coordinates of the tiles' four neighbors
        return filter(self.filter_tile_neighbors, neighbors)

    def in_bounds(self, coord: Vec2d):
        in_horizontal = 0 <= coord.x <= self.max_x
        in_vertical = 0 <= coord.y <= self.max_y
        return in_horizontal and in_vertical

    def filter_tile_neighbors(self, coord):
        """ Used to filter the tile to check if it is a neighbor of the tank.
        """
        if not self.in_bounds(coord):
            return False

        box_type = self.current_map.boxAt(*coord)
        return box_type == 0 or box_type == 2

