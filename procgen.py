"""
Este módulo genera mapas de mazmorras y coloca entidades como monstruos y objetos en el juego.
Proporciona funciones para crear salas, túneles, habitaciones secretas y gestionar probabilidades de aparición de entidades.
"""

from __future__ import annotations  # Permite la postergación de las anotaciones de tipo para evitar problemas con clases definidas más tarde.
from components.equippable import ChainMail # Importa la clase ChainMail para el equipo.
from game_map import GameMap  # Importa la clase GameMap, que maneja el mapa del juego.
from typing import Iterator, List, Tuple, TYPE_CHECKING, Dict  # Importación de tipos para la comprobación de tipos.

import tcod  # Importa la biblioteca tcod para gráficos y operaciones relacionadas con el juego.
import random  # Se importa para generar números aleatorios.
import entity_factories  # Importa las fábricas de entidades, donde se definen las entidades como pociones, monstruos, etc.
import tile_types  # Importa los tipos de tiles del juego, como el suelo, las paredes, etc.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:  
    from engine import Engine  
    from entity import Entity  

# Definición de los máximos posibles de ítems por nivel de piso.
max_items_by_floor = [
    (1, 1),  # A partir del nivel 1, máximo 1 ítem.
    (3, 2),  # A partir del nivel 3, máximo 2 ítems.
    (7, 3),  # A partir del nivel 5, máximo 3 ítems.
]

# Definición de los máximos posibles de monstruos por nivel de piso.
max_monsters_by_floor = [
    (1, 1),  # A partir del nivel 1, máximo 1 monstruo.
    (2, 2),  # A partir del nivel 2, máximo 2 monstruos.
    (4, 3),  # A partir del nivel 4, máximo 3 monstruos.
    (6, 5),  # A partir del nivel 6, máximo 5 monstruos.
]

# Probabilidades de que ciertos ítems aparezcan en niveles específicos.
item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],  # 35% de probabilidad de poción de salud.
    2: [(entity_factories.confusion_scroll, 10)],  # 10% de probabilidad de pergamino de confusión.
    4: [
        (entity_factories.lightning_scroll, 25),  # 25% de probabilidad de pergamino de relámpago.
        (entity_factories.sword, 10),  # 10% de probabilidad de espada.
        (entity_factories.defensive_scroll, 20),  # 20% de probabilidad de pergamino defensivo.
    ],
    6: [
        (entity_factories.health_potion, 0),  # 0% de probabilidad de poción de salud (no aparece)
        (entity_factories.fireball_scroll, 25),  # 25% de probabilidad de pergamino de bola de fuego
        (entity_factories.chain_mail, 15),  # 15% de probabilidad de cota de malla
        (entity_factories.greater_health_potion, 35),  # 35% de probabilidad de poción de salud mayor
    ],
}

# Probabilidades de que ciertos monstruos aparezcan en niveles específicos.
enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],  # 80% de probabilidad de orco en el nivel 0.
    2: [(entity_factories.goblin, 30)],  # 30% de probabilidad de goblin a partir del nivel 2.
    3: [(entity_factories.troll, 15)],  # 15% de probabilidad de troll a partir del nivel 3.
    5: [
        (entity_factories.troll, 30),  # 30% de probabilidad de troll.
        (entity_factories.goblin, 50),  # 50% de probabilidad de goblin.
    ],
    7: [
        (entity_factories.troll, 60),  # 60% de probabilidad de troll.
    ],
}

# Función para obtener el valor máximo de ítems o monstruos por nivel de piso.
def get_max_value_for_floor(
    weighted_chances_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    """Obtiene el valor máximo permitido para un piso dado."""
    current_value = 0

    for floor_minimum, value in weighted_chances_by_floor:
        if floor >= floor_minimum:
            current_value = value  # Actualiza el valor si el piso cumple con el mínimo.

    return current_value

# Función para obtener una lista de entidades aleatorias con una probabilidad ponderada.
def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    """Obtiene una lista de entidades aleatorias basadas en probabilidades ponderadas."""
    entity_weighted_chances = {}

    # Recorre las probabilidades de aparición por piso.
    for key, values in weighted_chances_by_floor.items():
        if key <= floor:  # Solo considera entidades para el piso actual o inferior.
            for entity, weight in values:
                entity_weighted_chances[entity] = entity_weighted_chances.get(entity, 0) + weight

    if not entity_weighted_chances:  # Si no hay entidades disponibles, retorna una lista vacía.
        return []

    entities = list(entity_weighted_chances.keys())
    entity_weights = list(entity_weighted_chances.values())

    # Selecciona entidades aleatoriamente según las probabilidades.
    return random.choices(entities, weights=entity_weights, k=number_of_entities)

# Clase que representa una sala rectangular en el mapa del juego.
class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x  # Coordenada X inicial de la sala.
        self.y1 = y  # Coordenada Y inicial de la sala.
        self.x2 = x + width  # Coordenada X final de la sala.
        self.y2 = y + height  # Coordenada Y final de la sala.

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
def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int) -> None:
    """Coloca enemigos y objetos en una habitación."""
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        for _ in range(10):  # Intenta encontrar una posición válida hasta 10 veces.
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)

            if dungeon.in_bounds(x, y) and not any(e.x == x and e.y == y for e in dungeon.entities):
                entity.spawn(dungeon, x, y)
                break

# Función para generar un túnel en forma de L entre dos puntos dados.
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Devuelve un túnel en forma de L entre los centros de las salas, dejando una pared de separación con las salas."""
    x1, y1 = start
    x2, y2 = end
    # Conectar solo al centro de la sala (ya ajustado por quien llama a esta función)
    if random.random() < 0.5:  # 50% de probabilidad.
        # Mueve horizontalmente, luego verticalmente.
        corner_x, corner_y = x2, y1
    else:
        # Mueve verticalmente, luego horizontalmente.
        corner_x, corner_y = x1, y2

    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y

# Función para generar habitaciones secretas conectadas a las habitaciones existentes.
def generate_secret_rooms(
    dungeon: GameMap, rooms: List[RectangularRoom], num_secrets: int, width: int = 6, height: int = 6
) -> None:
    """Genera habitaciones secretas con dimensiones fijas conectadas a las habitaciones existentes."""
    for _ in range(num_secrets):
        attempts = 0
        while attempts < 10:  # Intenta generar una habitación secreta hasta 10 veces.
            # Selecciona una habitación existente al azar para conectar la habitación secreta.
            parent_room = random.choice(rooms)

            # Determina la posición de la habitación secreta adyacente a la habitación principal.
            direction = random.choice(["N", "S", "E", "W"])
            if direction == "N":
                x1_start = parent_room.x1 + 1
                x1_end = parent_room.x2 - width - 1
                if x1_start > x1_end:  # Verifica si el rango es válido
                    attempts += 1
                    continue
                x1 = random.randint(x1_start, x1_end)
                y1 = parent_room.y1 - height - 1
            elif direction == "S":
                x1_start = parent_room.x1 + 1
                x1_end = parent_room.x2 - width - 1
                if x1_start > x1_end:  # Verifica si el rango es válido
                    attempts += 1
                    continue
                x1 = random.randint(x1_start, x1_end)
                y1 = parent_room.y2 + 1
            elif direction == "E":
                x1 = parent_room.x2 + 1
                y1_start = parent_room.y1 + 1
                y1_end = parent_room.y2 - height - 1
                if y1_start > y1_end:  # Verifica si el rango es válido
                    attempts += 1
                    continue
                y1 = random.randint(y1_start, y1_end)
            else:  # "W"
                x1 = parent_room.x1 - width - 1
                y1_start = parent_room.y1 + 1
                y1_end = parent_room.y2 - height - 1
                if y1_start > y1_end:  # Verifica si el rango es válido
                    attempts += 1
                    continue
                y1 = random.randint(y1_start, y1_end)

            x2 = x1 + width
            y2 = y1 + height

            # Verifica que las coordenadas sean válidas antes de crear la habitación secreta.
            if not dungeon.in_bounds(x1, y1) or not dungeon.in_bounds(x2 - 1, y2 - 1):
                attempts += 1
                continue

            # Verifica si la habitación secreta se superpone con otras habitaciones o pasillos.
            secret_room = RectangularRoom(x1, y1, width, height)
            if any(secret_room.intersects(other_room) for other_room in rooms):
                attempts += 1
                continue

            # Verifica si la habitación secreta se superpone con pasillos existentes.
            for x in range(secret_room.x1 + 1, secret_room.x2):
                for y in range(secret_room.y1 + 1, secret_room.y2):
                    if dungeon.tiles[x, y] == tile_types.floor:
                        attempts += 1
                        break
                else:
                    continue
                break
            else:
                # Marca todos los tiles de la habitación secreta como suelo.
                dungeon.tiles[secret_room.inner] = tile_types.floor
                rooms.append(secret_room)

                # Coloca un objeto específico en el centro de la habitación secreta.
                secret_item = entity_factories.invisibility_scroll  # Cambia este objeto según lo que desees generar.
                secret_item.spawn(dungeon, *secret_room.center)

                # Conecta la habitación secreta con la habitación principal.
                connect_secret_room(dungeon, parent_room, secret_room, direction)

                # Imprime un mensaje en la terminal indicando que se generó una habitación secreta.
                print(f"Se generó una habitación secreta en {secret_room.center} conectada a {parent_room.center}.")

                break  # Si se genera una habitación secreta válida, rompe el bucle.

# Función que conecta una habitación secreta a una habitación principal mediante un túnel.
def connect_secret_room(
    dungeon: GameMap, parent_room: RectangularRoom, secret_room: RectangularRoom, direction: str
) -> None:
    """Conecta una habitación secreta a una habitación principal mediante un túnel, dejando una pared de separación."""
    if direction == "N":
        door_x = (parent_room.x1 + parent_room.x2) // 2
        door_y = parent_room.y1
        tunnel_x, tunnel_y = door_x, secret_room.y2 - 1  # Deja una pared
    elif direction == "S":
        door_x = (parent_room.x1 + parent_room.x2) // 2
        door_y = parent_room.y2
        tunnel_x, tunnel_y = door_x, secret_room.y1  # Ya está a una pared
    elif direction == "E":
        door_x = parent_room.x2
        door_y = (parent_room.y1 + parent_room.y2) // 2
        tunnel_x, tunnel_y = secret_room.x1, door_y  # Ya está a una pared
    else:  # "W"
        door_x = parent_room.x1
        door_y = (parent_room.y1 + parent_room.y2) // 2
        tunnel_x, tunnel_y = secret_room.x2 - 1, door_y  # Deja una pared

    # Genera un túnel desde la puerta hasta el interior de la sala secreta
    for x, y in tunnel_between((door_x, door_y), (tunnel_x, tunnel_y)):
        dungeon.tiles[x, y] = tile_types.floor

    # Marca la puerta como un tile especial
    dungeon.tiles[door_x, door_y] = tile_types.door

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
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []  # Lista para almacenar las salas generadas.
    center_of_last_room = (0, 0)  # Centro de la última sala generada.

    for _ in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)  # Ancho aleatorio de la sala.
        room_height = random.randint(room_min_size, room_max_size)  # Altura aleatoria de la sala.

        x = random.randint(0, dungeon.width - room_width - 1)  # Coordenada X inicial.
        y = random.randint(0, dungeon.height - room_height - 1)  # Coordenada Y inicial.

        new_room = RectangularRoom(x, y, room_width, room_height)  # Crea una nueva sala.

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # Si la sala se superpone con otra, se descarta.

        dungeon.tiles[new_room.inner] = tile_types.floor  # Marca el área de la sala como suelo.

        if len(rooms) == 0:
            player.place(*new_room.center, dungeon)  # Coloca al jugador en el centro de la primera sala.
        else:
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor  # Crea un túnel entre salas.

        place_entities(new_room, dungeon, engine.game_world.current_floor)  # Coloca entidades.
        rooms.append(new_room)  # Añade la sala a la lista de salas.
        center_of_last_room = new_room.center  # Actualiza el centro de la última sala.

    # Genera habitaciones secretas después de las salas normales.
    generate_secret_rooms(dungeon, rooms, num_secrets=1, width=6, height=6)

    dungeon.tiles[center_of_last_room] = tile_types.down_stairs  # Coloca las escaleras hacia abajo.
    dungeon.downstairs_location = center_of_last_room  # Actualiza la ubicación de las escaleras.

    return dungeon  # Retorna el mapa generado.