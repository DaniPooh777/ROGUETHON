from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

# Importación condicional para las clases Actor e Item solo en tiempo de comprobación de tipos
if TYPE_CHECKING:
    from entity import Actor, Item  # Importa las clases Actor y Item para el tipo de 'parent' y 'items' en la clase Inventory


class Inventory(BaseComponent):
    """Componente que gestiona el inventario de un Actor."""

    parent: Actor  # Actor al que pertenece este componente de inventario

    def __init__(self, capacity: int):
        """Inicializa el inventario con una capacidad dada y una lista de objetos."""
        self.capacity = capacity  # Capacidad máxima del inventario
        self.items: List[Item] = []  # Lista de objetos que el actor tiene en el inventario

    def drop(self, item: Item) -> None:
        """
        Elimina un objeto del inventario y lo devuelve al mapa de juego, en la ubicación actual del actor.
        
        Este método es útil cuando el jugador quiere soltar un objeto de su inventario.
        """
        self.items.remove(item)  # Elimina el objeto del inventario

        # Coloca el objeto en las coordenadas actuales del actor en el mapa de juego
        item.place(self.parent.x, self.parent.y, self.gamemap)

        # Registra en el log del juego que el actor ha soltado el objeto
        self.engine.message_log.add_message(f"Has soltado {item.name}.")
