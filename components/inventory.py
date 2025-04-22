"""
La clase 'Inventory' gestiona el inventario de un actor en el juego, 
permitiéndole almacenar y soltar objetos. Se asocia a un actor específico 
que tiene una capacidad máxima de objetos.
"""

from __future__ import annotations # Permite usar anotaciones de tipo con cadenas para clases no definidas aún.
from typing import List, TYPE_CHECKING # Importa herramientas para el manejo de tipos en el código.
from components.base_component import BaseComponent # Importa la clase BaseComponent que será la clase base de todos los componentes

# Importación condicional para las clases Actor e Item solo durante la comprobación de tipos
if TYPE_CHECKING:
    # Aquí se importan las clases Actor y Item, ya que 'parent' y 'items' en la clase Inventory
    # requieren esos tipos para la validación de los tipos estáticos.
    from entity import Actor, Item  # Importa las clases Actor y Item para el tipo de 'parent' y 'items' en la clase Inventory

class Inventory(BaseComponent):
    """Componente que gestiona el inventario de un Actor."""

    parent: Actor  # Actor al que pertenece este componente de inventario

    def __init__(self, capacity: int):
        """
        Inicializa el inventario con una capacidad dada y una lista vacía de objetos.

        :param capacity: Capacidad máxima que puede contener el inventario.
        """
        self.capacity = capacity  # Capacidad máxima del inventario
        self.items: List[Item] = []  # Lista de objetos que el actor tiene en el inventario

    def drop(self, item: Item) -> None:
        """
        Elimina un objeto del inventario y lo devuelve al mapa de juego, en la ubicación actual del actor.
        
        Este método es útil cuando el jugador quiere soltar un objeto de su inventario.

        :param item: El objeto que se va a soltar.
        """
        # Elimina el objeto del inventario, lo cual modifica la lista de 'items'
        self.items.remove(item) 

        # Coloca el objeto en las coordenadas actuales del actor en el mapa de juego
        item.place(self.parent.x, self.parent.y, self.gamemap)

        # Registra en el log del juego que el actor ha soltado el objeto
        self.engine.message_log.add_message(f"Has soltado {item.name}.")
