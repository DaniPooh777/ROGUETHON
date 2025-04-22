"""
Este módulo define el orden de renderizado de las entidades en el juego.
El orden determina qué entidades se dibujan sobre otras en la consola.
"""

from enum import auto, Enum # Importa la clase Enum para definir enumeraciones.

# Clase que define el orden de renderizado de las entidades.
class RenderOrder(Enum):
    CORPSE = auto()  # Los cadáveres se renderizan primero, debajo de todo.
    ITEM = auto()  # Los ítems se renderizan encima de los cadáveres.
    ACTOR = auto()  # Los actores (jugador y enemigos) se renderizan encima de los ítems.
