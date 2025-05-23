"""
Este módulo define las clases Entity, Actor e Item, que representan objetos genéricos, personajes y objetos en el juego.
Proporciona métodos para manejar la posición, movimiento, y relaciones jerárquicas entre entidades y sus componentes.
"""

from __future__ import annotations  # Permite las anotaciones de tipo dentro de la misma clase.
from typing import Optional, Tuple, Type, TypeVar, Union, TYPE_CHECKING # Importa herramientas para la comprobación de tipos.
from render_order import RenderOrder # Importa el orden de renderizado para las entidades.

import copy # Importa el módulo copy para crear copias profundas de objetos.
import math # Importa el módulo math para operaciones matemáticas.
import color # Importa el módulo de colores personalizados.


# Esto es para evitar errores de referencia circular, ya que estos módulos se importan más abajo en el código.
if TYPE_CHECKING: 
    from components.ai import BaseAI 
    from components.consumable import Consumable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap
    from components.level import Level
    from components.equippable import Equippable
    from components.equipment import Equipment

# Definición de un tipo genérico T, que se usa para referirse a la clase Entity.
T = TypeVar("T", bound="Entity")

# La clase Entity representa cualquier objeto en el juego (jugador, enemigo, ítem, etc.).
class Entity:
    """
    Un objeto genérico para representar jugadores, enemigos, ítems, etc.
    """

    parent: Union[GameMap, Inventory]  # El objeto al que pertenece (puede ser un mapa o inventario).

    def __init__(
        self,
        parent: Optional[GameMap] = None,  # El padre es opcional, por defecto None
        x: int = 0,  # Posición X en el mapa
        y: int = 0,  # Posición Y en el mapa
        char: str = "?",  # Carácter que representa al objeto
        color: Tuple[int, int, int] = (255, 255, 255),  # Color del objeto
        name: str = "<Unnamed>",  # Nombre del objeto
        blocks_movement: bool = False,  # Si bloquea o no el movimiento
        render_order: RenderOrder = RenderOrder.CORPSE,  # Orden de renderizado (cómo se dibuja)
    ):
        # Inicialización de las propiedades del objeto
        self.x = x  # Coordenada X del objeto
        self.y = y  # Coordenada Y del objeto
        self.char = char  # Carácter que representa al objeto
        self.color = color  # Color del objeto
        self.name = name  # Nombre del objeto
        self.blocks_movement = blocks_movement  # Si bloquea el movimiento
        self.render_order = render_order  # Orden de renderizado
        
        # Si el objeto tiene un padre (por ejemplo, un mapa), se lo asigna
        if parent:
            self.parent = parent  # Asigna el padre
            parent.entities.add(self)  # Añade este objeto a la lista de entidades del padre

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap  # Devuelve el mapa de juego al que pertenece el objeto

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Crea una copia del objeto y lo coloca en una nueva ubicación."""
        clone = copy.deepcopy(self)  # Crea una copia profunda del objeto
        clone.x = x  # Asigna la nueva posición
        clone.y = y
        clone.parent = gamemap  # Asigna el nuevo mapa como el padre
        gamemap.entities.add(clone)  # Añade el clon al mapa de juego
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Coloca este objeto en una nueva ubicación dentro del mapa."""
        self.x = x  # Actualiza la posición X
        self.y = y  # Actualiza la posición Y
        if gamemap:
            if hasattr(self, "parent"):  # Verifica si el objeto tiene un padre
                if self.parent is self.gamemap:  # Si el padre es el mapa actual
                    self.gamemap.entities.remove(self)  # Elimina al objeto del mapa anterior
            self.parent = gamemap  # Asigna el nuevo mapa como padre
            gamemap.entities.add(self)  # Añade el objeto al nuevo mapa

    def distance(self, x: int, y: int) -> float:
        """
        Devuelve la distancia entre este objeto y un punto dado en el mapa.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)  # Calcula la distancia euclidiana

    def move(self, dx: int, dy: int) -> None:
        # Mueve el objeto por una cantidad dada de píxeles (dx, dy)
        self.x += dx  # Actualiza la posición X
        self.y += dy  # Actualiza la posición Y


# La clase Actor hereda de Entity y representa personajes jugables o enemigos.
class Actor(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],  # Tipo de IA asociada con este actor
        equipment: Equipment,  # Equipo del actor
        fighter: Fighter,  # Componentes de lucha del actor
        inventory: Inventory,  # Inventario del actor
        level: Level,  # Nivel del actor
    ):
        super().__init__(  # Llamada al constructor de la clase base (Entity)
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,  # Los actores bloquean el movimiento
            render_order=RenderOrder.ACTOR,  # Los actores se dibujan con el orden correspondiente
        )

        # Inicialización de las propiedades específicas de Actor
        self.ai: Optional[BaseAI] = ai_cls(self)  # Instancia la IA del actor
        self.equipment: Equipment = equipment  # Asigna el equipo
        self.equipment.parent = self  # Asigna el actor como el "padre" del equipo

        self.fighter = fighter  # Asigna el componente de luchador
        self.fighter.parent = self  # Asigna el actor como "padre" del luchador

        self.inventory = inventory  # Asigna el inventario
        self.inventory.parent = self  # Asigna el actor como "padre" del inventario

        self.level = level  # Asigna el nivel
        self.level.parent = self  # Asigna el actor como "padre" del nivel

        self.invisibility_turns = 0  # Contador de turnos de invisibilidad

    @property
    def invisible(self) -> bool:
        """Devuelve True si el jugador está invisible."""
        return self.invisibility_turns > 0

    @property
    def is_alive(self) -> bool:
        """Devuelve True si este actor está vivo y puede realizar acciones."""
        return bool(self.ai)  # Un actor está vivo si tiene una IA asociada.


# La clase Item también hereda de Entity y representa objetos consumibles, armamentos, etc.
class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: Optional[Consumable] = None,  # El objeto es consumible si se especifica
        equippable: Optional[Equippable] = None,  # El objeto es equipable si se especifica
    ):
        super().__init__(  # Llamada al constructor de la clase base (Entity)
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,  # Los ítems no bloquean el movimiento
            render_order=RenderOrder.ITEM,  # Los ítems se dibujan en un orden diferente
        )

        self.consumable = consumable  # Asigna el objeto consumible
        if self.consumable:
            self.consumable.parent = self  # Asigna el ítem como "padre" del consumible

        self.equippable = equippable  # Asigna el objeto equipable

        if self.equippable:
            self.equippable.parent = self  # Asigna el ítem como "padre" del equipable


def handle_enemy_turns(self) -> None:
    """Maneja los turnos de los enemigos y reduce el contador de invisibilidad del jugador."""
    if self.player.invisibility_turns > 0:
        self.player.invisibility_turns -= 1
        if self.player.invisibility_turns == 0:
            self.message_log.add_message(
                f"{self.player.name} vuelve a ser visible.",
                color.status_effect_applied,
            )

    for entity in set(self.game_map.actors) - {self.player}:
        if entity.ai:
            entity.ai.perform()