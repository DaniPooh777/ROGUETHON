# Importa futuras características de Python y herramientas de tipado.
from __future__ import annotations

# Importa tipos de datos para anotaciones de tipo y chequeo de tipos en tiempo de desarrollo.
from typing import Iterable, Iterator, Optional, TYPE_CHECKING

# Importa la librería numpy para manipular arrays de forma eficiente.
import numpy as np  # type: ignore
# Importa la clase Console de tcod para renderizar la consola en pantalla.
from tcod.console import Console

# Importa las clases Actor, Item y otros tipos necesarios del archivo 'entity'.
from entity import Actor, Item
import tile_types  # Importa tipos de tile, como 'wall' y 'SHROUD'.

# Si TYPE_CHECKING está activo, realiza importaciones para chequear tipos.
if TYPE_CHECKING:
    from engine import Engine  # Importa la clase Engine.
    from entity import Entity  # Importa la clase Entity.


# Clase que representa el mapa del juego.
class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        # Inicializa el mapa con sus dimensiones, entidades y tiles.
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)  # Conjunto de entidades en el mapa.
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")  # Mapa de tiles, por defecto todo es una pared.

        # Matrices que controlan lo que el jugador puede ver y lo que ha explorado.
        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles que el jugador puede ver actualmente.
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles que el jugador ha visto previamente.

        self.downstairs_location = (0, 0)  # Ubicación de las escaleras hacia abajo.

    @property
    def gamemap(self) -> GameMap:
        # Propiedad que devuelve el objeto 'GameMap' actual.
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Devuelve un iterador sobre los actores vivos en el mapa."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive  # Solo actores vivos.
        )

    @property
    def items(self) -> Iterator[Item]:
        """Devuelve un iterador sobre los ítems en el mapa."""
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        """Devuelve una entidad que bloquea el movimiento en una ubicación dada, si existe."""
        for entity in self.entities:
            if (
                entity.blocks_movement  # Si la entidad bloquea el movimiento.
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity  # Retorna la entidad bloqueadora.
        return None  # Si no hay entidad bloqueando, retorna None.

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        """Devuelve el actor en una ubicación dada, si existe."""
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor  # Retorna el actor en esa posición.
        return None  # Si no hay actor, retorna None.

    def in_bounds(self, x: int, y: int) -> bool:
        """Retorna True si las coordenadas (x, y) están dentro de los límites del mapa."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Renderiza el mapa en la consola.

        Si un tile está en la matriz "visible", se dibuja con los colores "light".
        Si no está visible, pero ha sido explorado, se dibuja con los colores "dark".
        Si no ha sido explorado, se dibuja como "SHROUD".
        """
        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],  # Condiciones para elegir los colores.
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,  # Si no se cumplen las condiciones, usa "SHROUD".
        )

        # Ordena las entidades por su valor de renderizado para dibujarlas en el orden correcto.
        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        # Dibuja cada entidad que sea visible.
        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, string=entity.char, fg=entity.color
                )

# Clase que gestiona el mundo del juego, incluyendo la generación de mapas y el manejo de pisos.
class GameWorld:
    """
    Contiene las configuraciones para el GameMap y genera nuevos mapas cuando se bajan las escaleras.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ):
        # Inicializa el mundo del juego con sus parámetros.
        self.engine = engine
        self.map_width = map_width
        self.map_height = map_height
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from procgen import generate_dungeon  # Importa la función para generar el dungeon.

        self.current_floor += 1  # Aumenta el número de piso cuando se genera uno nuevo.

        # Llama a la función para generar el nuevo mapa del dungeon y lo asigna al mapa del motor.
        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
        )