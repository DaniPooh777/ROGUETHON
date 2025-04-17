from __future__ import annotations  # Permite la postergación de las anotaciones de tipo para evitar problemas con clases definidas más tarde.

import random  # Se importa para generar números aleatorios.

from typing import Iterator, List, Tuple, TYPE_CHECKING, Dict  # Importación de tipos para la comprobación de tipos.

import tcod  # Importa la biblioteca tcod para gráficos y operaciones relacionadas con el juego.

from components.equippable import ChainMail
import entity_factories  # Importa las fábricas de entidades, donde se definen las entidades como pociones, monstruos, etc.
from game_map import GameMap  # Importa la clase GameMap, que maneja el mapa del juego.
import tile_types  # Importa los tipos de tiles del juego, como el suelo, las paredes, etc.


if TYPE_CHECKING:  # Esto solo es útil en tiempo de comprobación de tipos, no afecta al código en ejecución.
    from engine import Engine  # Importa la clase Engine para interactuar con la lógica del juego.
    from entity import Entity  # Importa la clase Entity para manejar a los personajes y objetos del juego.


# Definición de los máximos posibles de ítems por nivel de piso.
max_items_by_floor = [
    (1, 1),
    (3, 2),
    (5, 3),
]

# Definición de los máximos posibles de monstruos por nivel de piso.
max_monsters_by_floor = [
    (1, 1),
    (2, 2),
    (4, 3),
    (6, 5),
]

# Probabilidades de que ciertos ítems aparezcan en niveles específicos.
item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],  # 35% de probabilidad de que aparezca una poción de salud en el nivel 0.
    2: [(entity_factories.confusion_scroll, 10)],  # 10% de probabilidad de que aparezca un pergamino de confusión en el nivel 2.
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 10), (entity_factories.defensive_scroll, 20)],  # 25% de probabilidad para un pergamino de rayos y 5% para una espada en el nivel 4.
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],  # 25% de probabilidad para un pergamino de bola de fuego y 15% para una cota de malla en el nivel 6.
}

# Probabilidades de que ciertos monstruos aparezcan en niveles específicos.
enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],  # Orco.
    2: [(entity_factories.goblin, 30)],  # Goblin aparece a partir del nivel 2.
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30), (entity_factories.goblin, 50)],  # Más goblins en niveles superiores.
    7: [(entity_factories.troll, 60)],
}

# Función para obtener el valor máximo de ítems o monstruos por nivel de piso.
def get_max_value_for_floor(
    weighted_chances_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0  # Valor por defecto, si no se encuentra otro.

    # Recorre las probabilidades de aparición por piso.
    for floor_minimum, value in weighted_chances_by_floor:
        if floor_minimum > floor:
            break  # Si el nivel mínimo es mayor que el piso actual, se detiene la búsqueda.
        else:
            current_value = value  # Si no, actualiza el valor con el valor de ese piso.

    return current_value  # Devuelve el valor máximo para ese piso.


# Función para obtener una lista de entidades aleatorias con una probabilidad ponderada.
def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}  # Diccionario para almacenar entidades y sus probabilidades.

    # Recorre las probabilidades de aparición por piso.
    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break  # Si el piso es mayor que el actual, se detiene.
        else:
            for value in values:
                entity = value[0]  # La entidad.
                weighted_chance = value[1]  # La probabilidad de que aparezca.

                entity_weighted_chances[entity] = weighted_chance  # Almacena la entidad y su probabilidad.

    entities = list(entity_weighted_chances.keys())  # Lista de entidades disponibles.
    entity_weighted_chance_values = list(entity_weighted_chances.values())  # Probabilidades asociadas.

    # Elige las entidades aleatoriamente según las probabilidades.
    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities  # Devuelve las entidades elegidas.


# Clase que representa una sala rectangular en el mapa del juego.
class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """Devuelve el centro de la sala."""
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Devuelve el área interna de la sala como un índice de arreglo 2D."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Devuelve True si esta sala se superpone con otra."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


# Función que coloca entidades (monstruos y objetos) en una sala.
def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    # Calcula el número de monstruos y objetos en función del nivel del piso.
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )
    
    # Obtiene una lista de monstruos y objetos según las probabilidades de aparición.
    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    # Coloca las entidades en posiciones aleatorias dentro de la sala.
    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        # Verifica si el espacio está libre de otras entidades.
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)  # Si está libre, coloca la entidad.


# Función para generar un túnel en forma de L entre dos puntos dados.
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Devuelve un túnel en forma de L entre estos dos puntos."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% de probabilidad.
        # Mueve horizontalmente, luego verticalmente.
        corner_x, corner_y = x2, y1
    else:
        # Mueve verticalmente, luego horizontalmente.
        corner_x, corner_y = x1, y2

    # Genera las coordenadas para este túnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_secret_rooms(dungeon: GameMap, rooms: List[RectangularRoom], num_secrets: int, min_size: int = 4, max_size: int = 6) -> None:
    """Genera habitaciones secretas conectadas a las habitaciones existentes mediante paredes falsas.
    Las dimensiones de las salas secretas están limitadas por `min_size` y `max_size`.
    """
    for _ in range(num_secrets):
        # Selecciona una habitación existente al azar para conectar la habitación secreta.
        parent_room = random.choice(rooms)

        # Genera una nueva habitación secreta con dimensiones aleatorias dentro de los límites.
        secret_width = random.randint(min_size, max_size)
        secret_height = random.randint(min_size, max_size)

        # Determina la posición de la habitación secreta adyacente a la habitación principal.
        direction = random.choice(["N", "S", "E", "W"])
        if direction == "N":
            secret_x = parent_room.x1 + 1
            secret_y = parent_room.y1 - secret_height - 1
        elif direction == "S":
            secret_x = parent_room.x1 + 1
            secret_y = parent_room.y2 + 1
        elif direction == "E":
            secret_x = parent_room.x2 + 1
            secret_y = parent_room.y1 + 1
        else:  # "W"
            secret_x = parent_room.x1 - secret_width - 1
            secret_y = parent_room.y1 + 1

        # Verifica que las coordenadas sean válidas antes de crear la habitación secreta.
        if not dungeon.in_bounds(secret_x, secret_y) or not dungeon.in_bounds(secret_x + secret_width - 1, secret_y + secret_height - 1):
            continue

        # Asegúrate de que las dimensiones cumplan con los valores mínimos y máximos.
        if secret_width < min_size or secret_width > max_size or secret_height < min_size or secret_height > max_size:
            continue

        secret_room = RectangularRoom(secret_x, secret_y, secret_width, secret_height)

        # Asegúrate de que la habitación secreta no se superponga con otras habitaciones o pasillos.
        if any(secret_room.intersects(other_room) for other_room in rooms):
            continue

        # Verifica que la habitación secreta no se superponga con pasillos normales.
        for x in range(secret_room.x1, secret_room.x2 + 1):
            for y in range(secret_room.y1, secret_room.y2 + 1):
                if dungeon.tiles[x, y] == tile_types.floor:
                    break
            else:
                continue
            break
        else:
            # Marca la habitación secreta como suelo y elimina cualquier pared interna.
            for x in range(secret_room.x1, secret_room.x2 + 1):
                for y in range(secret_room.y1, secret_room.y2 + 1):
                    dungeon.tiles[x, y] = tile_types.floor

            # Conecta la habitación secreta con la habitación principal mediante una pared falsa.
            connect_secret_room(dungeon, parent_room, secret_room, direction)

            # Añade la habitación secreta a la lista de habitaciones.
            rooms.append(secret_room)

            # Genera un objeto específico (poción de salud) en el centro de la habitación secreta.
            center_x, center_y = secret_room.center
            entity_factories.chain_mail.spawn(dungeon, center_x, center_y)

            # Mensaje de depuración para verificar la generación.
            print(f"Habitación secreta generada en: ({secret_x}, {secret_y}) con dimensiones ({secret_width}x{secret_height}) y poción de salud en el centro ({center_x}, {center_y})")

def connect_secret_room(dungeon: GameMap, parent_room: RectangularRoom, secret_room: RectangularRoom, direction: str) -> None:
    """Conecta una habitación secreta a una habitación principal mediante una pared falsa."""
    if direction == "N":
        wall_x = random.randint(parent_room.x1 + 1, parent_room.x2 - 1)
        wall_y = parent_room.y1
        tunnel_x, tunnel_y = wall_x, wall_y - 1
    elif direction == "S":
        wall_x = random.randint(parent_room.x1 + 1, parent_room.x2 - 1)
        wall_y = parent_room.y2
        tunnel_x, tunnel_y = wall_x, wall_y + 1
    elif direction == "E":
        wall_x = parent_room.x2
        wall_y = random.randint(parent_room.y1 + 1, parent_room.y2 - 1)
        tunnel_x, tunnel_y = wall_x + 1, wall_y
    else:  # "W"
        wall_x = parent_room.x1
        wall_y = random.randint(parent_room.y1 + 1, parent_room.y2 - 1)
        tunnel_x, tunnel_y = wall_x - 1, wall_y

    # Marca el túnel como suelo.
    dungeon.tiles[tunnel_x, tunnel_y] = tile_types.floor

    # Marca la pared falsa en la habitación principal.
    dungeon.tiles[wall_x, wall_y] = tile_types.hidden_wall_tile


# Función que genera un mapa de mazmorras.
def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Genera un nuevo mapa de mazmorras."""
    player = engine.player  # Obtiene al jugador.
    dungeon = GameMap(engine, map_width, map_height, entities=[player])  # Crea el mapa de mazmorras.

    rooms: List[RectangularRoom] = []  # Lista de salas generadas.
    center_of_last_room = (0, 0)  # Centro de la última sala generada.

    # Intenta generar hasta 'max_rooms' salas.
    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # Crea una nueva sala rectangular.
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Verifica si la nueva sala se superpone con alguna existente.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # Si se superpone, intenta con una nueva sala.

        # Si no hay superposición, se graba el espacio de la sala.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # La primera sala donde empieza el jugador.
            player.place(*new_room.center, dungeon)
        else:  # Para las salas siguientes.
            # Dibuja un túnel entre la última sala y la nueva.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

                center_of_last_room = new_room.center  # Actualiza el centro de la última sala.

        place_entities(new_room, dungeon, engine.game_world.current_floor)  # Coloca las entidades.

        rooms.append(new_room)

    # Genera habitaciones secretas.
    generate_secret_rooms(dungeon, rooms, num_secrets=2)

    dungeon.tiles[center_of_last_room] = tile_types.down_stairs  # Coloca las escaleras en el centro de la última sala.
    dungeon.downstairs_location = center_of_last_room  # Marca la ubicación de las escaleras.

    return dungeon  # Devuelve el mapa de mazmorras generado.
