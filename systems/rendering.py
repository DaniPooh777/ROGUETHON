"""
Este módulo gestiona el renderizado de elementos en la consola del juego, como barras de salud, nombres de entidades y niveles de mazmorras.
Proporciona funciones para mostrar información relevante al jugador de manera visual y clara.
"""

from __future__ import (
    annotations,
)  # Permite la postergación de las anotaciones de tipo, útil para evitar referencias circulares.
from typing import (
    TYPE_CHECKING,
    Tuple,
)  # IMPORTA: TYPE_CHECKING ayuda con las verificaciones de tipos en tiempo de análisis, y Tuple es para tuplas con tipos definidos.

if TYPE_CHECKING:
    from core.game_map import GameMap

from ui import colors as color  # Importa el módulo de colores personalizados.
import components.ai  # Importa el módulo de IA para verificar efectos de confusión.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from tcod import (
        Console,
    )  # Trae el tipo Console de tcod solo en tiempo de verificación.
    from core.engine import (
        Engine,
    )  # Trae el tipo Engine de engine solo en tiempo de verificación.
    from core.game_map import (
        GameMap,
    )  # Trae el tipo GameMap de game_map solo en tiempo de verificación.
    from components.fighter import Fighter
    from entities.entity import Actor


def get_names_at_location(x: int, y: int, game_map: GameMap) -> list:
    """
    Obtiene los nombres y colores de las entidades en la ubicación (x, y) en el mapa del juego,
    si están dentro del alcance visible del jugador.
    """
    if (
        not game_map.in_bounds(x, y) or not game_map.visible[x, y]
    ):  # Si la posición no está en los límites o no es visible, no se muestra nada.
        return []

    # Retorna lista de tuplas (nombre, color) para cada entidad en esa posición
    return [
        (entity.name, entity.color)
        for entity in game_map.entities
        if entity.x == x and entity.y == y
    ]


def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: "Engine"
) -> None:
    """Renderiza los nombres de las entidades en la posición del mouse con sus colores."""
    mouse_x, mouse_y = engine.mouse_location

    entities = get_names_at_location(x=mouse_x, y=mouse_y, game_map=engine.game_map)

    if not entities:
        return

    # Renderizar cada nombre con su color
    for i, (name, color) in enumerate(entities):
        console.print(x=x, y=y + i, string=name.capitalize(), fg=color)


def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    """
    Dibuja una barra de progreso para mostrar la salud del jugador (o alguna otra métrica) en la consola.
    """
    bar_width = int(
        float(current_value) / maximum_value * total_width
    )  # Calcula el ancho de la barra en función del valor actual.

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


def render_xp_bar(
    console: Console, current_xp: int, xp_to_next_level: int, total_width: int
) -> None:
    """
    Dibuja una barra de experiencia para mostrar el progreso hacia el siguiente nivel.
    """
    if xp_to_next_level == 0:
        bar_width = 0
    else:
        bar_width = int(float(current_xp) / xp_to_next_level * total_width)

    # Dibuja el fondo vacío de la barra de XP.
    console.draw_rect(x=0, y=46, width=20, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:
        console.draw_rect(x=0, y=46, width=bar_width, height=1, ch=1, bg=(0, 0, 200))

    # Imprime el texto con los valores de XP en la barra.
    console.print(
        x=1, y=46, string=f"XP: {current_xp}/{xp_to_next_level}", fg=color.bar_text
    )


def render_dungeon_level(
    console: Console, dungeon_level: int, location: Tuple[int, int]
) -> None:
    """
    Renderiza el nivel de la mazmorras en el que el jugador se encuentra, mostrando el nivel
    en la ubicación dada en la consola.
    """
    x, y = location  # Desempaqueta las coordenadas de la ubicación.

    console.print(
        x=x, y=y, string=f""" Piso: {dungeon_level}"""
    )  # Imprime el nivel de la mazmorras en la consola.


def render_status_effects(console: Console, game_map: "GameMap") -> None:
    """
    Renderiza los efectos activos de todos los actores en un panel con marco.
    Muestra los turnos restantes de invisibilidad, bono de defensa y modo defensivo.
    También muestra el estado de hambre del jugador.
    """
    from components.fighter import Fighter

    # Colores basados en los pergaminos correspondientes
    COLOR_INVISIBILITY = (128, 128, 255)  # Azul - Pergamino invisible
    COLOR_DEFENSE = (0, 191, 255)  # Azul claro - Pergamino defensivo
    COLOR_IMMUNITY = (255, 165, 0)  # Naranja - Pergamino de inmunidad
    COLOR_CONFUSION = (207, 63, 255)  # Púrpura - Pergamino de confusión
    COLOR_NO_EFFECT = (128, 128, 128)  # Gris - Sin efectos
    COLOR_ENEMY = (255, 100, 100)  # Rojo claro - Efectos de enemigos
    
    # Colores para estado de hambre
    COLOR_SATISFIED = (100, 255, 100)  # Verde
    COLOR_HUNGRY = (255, 255, 100)  # Amarillo
    COLOR_WEAK = (255, 165, 0)  # Naranja
    COLOR_MORIBUND = (255, 50, 50)  # Rojo

    # Recolectar efectos activos de todos los actores
    effects = []
    
    # Agregar estado de hambre del jugador
    player = game_map.engine.player
    if hasattr(player, 'hunger'):
        hunger_state = player.hunger.state
        hunger_value = player.hunger.current_hunger
        
        # No mostrar "Satisfecho", solo los demás estados
        if hunger_state == "hungry":
            effects.append((COLOR_HUNGRY, f"Hambriento ({hunger_value})"))
        elif hunger_state == "weak":
            effects.append((COLOR_WEAK, f"Debil ({hunger_value})"))
        elif hunger_state == "moribund":
            effects.append((COLOR_MORIBUND, f"Moribundo! ({hunger_value})"))

    for actor in game_map.actors:
        fighter = actor.fighter
        if fighter is None:
            continue

        if actor.invisibility_turns > 0:
            effects.append(
                (COLOR_INVISIBILITY, f"Invisibilidad {actor.invisibility_turns}")
            )
        if fighter.defense_bonus_turns > 0:
            effects.append((COLOR_DEFENSE, f"Defensa {fighter.defense_bonus_turns}"))
        if fighter.defensive_turns > 0:
            effects.append((COLOR_IMMUNITY, f"Inmunidad {fighter.defensive_turns}"))

        # Mostrar efectos de confusión en enemigos
        if isinstance(actor.ai, components.ai.ConfusedEnemy):
            effects.append((COLOR_CONFUSION, f"Confusion {actor.ai.turns_remaining}"))

    # Marco con altura fija
    frame_width = 24
    frame_height = 5  # Altura fija
    frame_x = 55
    frame_y = 44

    # Dibujar el marco con borde
    console.draw_frame(
        x=frame_x,
        y=frame_y,
        width=frame_width,
        height=frame_height,
        title=" ESTADOS ",
        clear=False,
        fg=color.menu_text,
        bg=color.black,
    )

    # Mostrar los efectos o mensaje de "sin efectos"
    if effects:
        # Mostrar hasta 2 efectos por línea
        lines = []
        for i in range(0, len(effects), 2):
            line = "  ".join([text for _, text in effects[i : i + 2]])
            lines.append(line)

        # Mostrar cada línea
        for i, line in enumerate(lines):
            if i < frame_height - 1:  # No exceder la altura del marco
                console.print(
                    x=frame_x + 1,
                    y=frame_y + 1 + i,
                    string=line,
                    fg=color.menu_text,
                )
    else:
        console.print(
            x=frame_x + 1,
            y=frame_y + 1,
            string="Sin efectos activos",
            fg=COLOR_NO_EFFECT,
        )


def render_tooltip(
    console: Console, game_map: "GameMap", mouse_x: int, mouse_y: int
) -> None:
    """
    Renderiza un tooltip con el nombre de la entidad bajo el mouse.
    Se muestra solo si hay una entidad visible o conocida en esa posición.
    """
    if not game_map.in_bounds(mouse_x, mouse_y):
        return

    # Buscar entidades en la posición del mouse
    entities_at_pos = [
        entity
        for entity in game_map.entities
        if entity.x == mouse_x and entity.y == mouse_y
    ]

    if not entities_at_pos:
        return

    # Obtener los nombres de las entidades
    names = [entity.name for entity in entities_at_pos]
    tooltip_text = ", ".join(names)

    if not tooltip_text:
        return

    # Calcular posición del tooltip (a la derecha del cursor, si no cabe, a la izquierda)
    tooltip_width = len(tooltip_text) + 2
    tooltip_height = 2

    tooltip_x = mouse_x + 1
    tooltip_y = mouse_y

    # Ajustar si se sale de la pantalla
    if tooltip_x + tooltip_width > console.width - 1:
        tooltip_x = mouse_x - tooltip_width - 1
    if tooltip_y + tooltip_height > console.height - 1:
        tooltip_y = mouse_y - tooltip_height

    # Asegurar que no tenga coordenadas negativas
    tooltip_x = max(1, tooltip_x)
    tooltip_y = max(1, tooltip_y)

    # Dibujar el fondo del tooltip
    console.draw_rect(
        x=tooltip_x,
        y=tooltip_y,
        width=tooltip_width,
        height=tooltip_height,
        ch=ord(" "),
        bg=(20, 20, 30),  # Fondo oscuro
    )

    # Dibujar el borde
    console.draw_frame(
        x=tooltip_x,
        y=tooltip_y,
        width=tooltip_width,
        height=tooltip_height,
        title="",
        clear=False,
        fg=(180, 180, 180),
    )

    # Escribir el nombre
    console.print(
        x=tooltip_x + 1,
        y=tooltip_y + 1,
        string=tooltip_text,
        fg=(255, 255, 100),  # Color amarillo dorado
    )
