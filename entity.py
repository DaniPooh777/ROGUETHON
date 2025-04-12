from __future__ import annotations  # Permite las anotaciones de tipo dentro de la misma clase.

# Importación de bibliotecas y módulos necesarios.
import copy
import math
from typing import Optional, Tuple, Type, TypeVar, Union, TYPE_CHECKING

# Se importa RenderOrder desde un módulo externo, probablemente usado para determinar el orden de dibujo de los objetos.
from render_order import RenderOrder

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
    A generic object to represent players, enemies, items, etc.
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
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        
        # Si el objeto tiene un padre (por ejemplo, un mapa), se lo asigna
        if parent:
            self.parent = parent
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
        self.x = x
        self.y = y
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
        self.x += dx
        self.y += dy


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