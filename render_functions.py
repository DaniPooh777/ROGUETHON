"""
Este módulo gestiona el renderizado de elementos en la consola del juego, como barras de salud, nombres de entidades y niveles de mazmorras.
Proporciona funciones para mostrar información relevante al jugador de manera visual y clara.
"""

from __future__ import annotations  # Permite la postergación de las anotaciones de tipo, útil para evitar referencias circulares.
from typing import TYPE_CHECKING, Tuple  # IMPORTA: TYPE_CHECKING ayuda con las verificaciones de tipos en tiempo de análisis, y Tuple es para tuplas con tipos definidos.

import color  # Importa el módulo de colores personalizados.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from tcod import Console  # Trae el tipo Console de tcod solo en tiempo de verificación.
    from engine import Engine  # Trae el tipo Engine de engine solo en tiempo de verificación.
    from game_map import GameMap  # Trae el tipo GameMap de game_map solo en tiempo de verificación.


def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    """
    Obtiene los nombres de las entidades en la ubicación (x, y) en el mapa del juego, 
    si están dentro del alcance visible del jugador.
    """
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:  # Si la posición no está en los límites o no es visible, no se muestra nada.
        return ""

    # Filtra las entidades que están en la misma posición (x, y) y junta sus nombres en una cadena separada por comas.
    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()  # Capitaliza la primera letra del nombre para presentación.


def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    """
    Dibuja una barra de progreso para mostrar la salud del jugador (o alguna otra métrica) en la consola.
    """
    bar_width = int(float(current_value) / maximum_value * total_width)  # Calcula el ancho de la barra en función del valor actual.

    # Dibuja el fondo vacío de la barra.
    console.draw_rect(x=0, y=45, width=20, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:  # Si hay algo de llenado en la barra, dibuja la parte llena.
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    # Imprime el texto con los valores de salud en la barra.
    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )


def render_dungeon_level(
    console: Console, dungeon_level: int, location: Tuple[int, int]
) -> None:
    """
    Renderiza el nivel de la mazmorras en el que el jugador se encuentra, mostrando el nivel
    en la ubicación dada en la consola.
    """
    x, y = location  # Desempaqueta las coordenadas de la ubicación.

    console.print(x=x, y=y, string=f""" Piso: {dungeon_level}""")  # Imprime el nivel de la mazmorras en la consola.


def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    """
    Muestra los nombres de las entidades en la ubicación del ratón en la consola.
    """
    mouse_x, mouse_y = engine.mouse_location  # Obtiene las coordenadas del ratón.

    # Llama a la función para obtener los nombres de las entidades en la posición del ratón.
    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    # Imprime los nombres en la consola en la ubicación dada.
    console.print(x=x, y=y, string=names_at_mouse_location)