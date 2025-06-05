"""
Este módulo gestiona la lógica principal del juego, incluyendo el manejo de turnos, eventos, renderizado y guardado de partidas.
"""

from __future__ import annotations  # Permite la anotación de tipos con clases que aún no están definidas.
from typing import TYPE_CHECKING, Callable  # Importa TYPE_CHECKING para la comprobación de tipos en tiempo de desarrollo.
from tcod.console import Console  # Importa la clase Console de la biblioteca tcod para la salida gráfica.
from tcod.map import compute_fov  # Importa compute_fov para calcular el campo de visión (FOV).
from components.base_component import BaseComponent  # Importa la clase base para componentes.
from message_log import MessageLog  # Importa el sistema de registro de mensajes.

import lzma  # Importa el módulo lzma para la compresión de datos.
import pickle  # Importa el módulo pickle para la serialización de objetos.
import tcod  # Importa la biblioteca tcod para gráficos y operaciones relacionadas con el juego.
import tcod.event  # Asegúrate de que tcod.event esté importado
import color  # Importa el módulo de colores personalizados.
import exceptions  # Importa las excepciones personalizadas.
import render_functions  # Importa funciones de renderizado personalizadas.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from entity import Actor  # Importa la clase Actor (para el jugador y enemigos).
    from game_map import GameMap, GameWorld  # Importa las clases GameMap y GameWorld.

# Clase principal que gestiona la lógica del juego.
class Engine:
    game_map: GameMap  # El mapa actual del juego.
    game_world: GameWorld  # El mundo de juego (contiene varios niveles).

    def __init__(self, player: Actor, context: tcod.context.Context, console: tcod.Console):
        """Inicializa el motor del juego con el jugador, contexto y consola."""
        self.message_log = MessageLog()  # Crea un objeto para registrar los mensajes del juego.
        self.player = player  # Asigna el jugador al motor del juego.
        self.context = context  # Asigna el contexto de tcod.
        self.console = console  # Asigna la consola de tcod.
        self.turn_count = 0  # Inicializa el contador de turnos en 0
        self.scheduled_tasks = []  # Lista para almacenar tareas programadas
        self.last_player_name = player.name  # Guarda el nombre del jugador inicial

    def schedule_task(self, turns: int, callback: Callable) -> None:
        """Programa una tarea para ejecutarse después de un número de turnos."""
        self.scheduled_tasks.append((self.turn_count + turns, callback))

    def process_scheduled_tasks(self) -> None:
        """Procesa y ejecuta las tareas programadas si es el turno adecuado."""
        current_turn = self.turn_count  # Obtiene el turno actual.
        for task in list(self.scheduled_tasks):  # Itera sobre las tareas programadas.
            task_turn, callback = task  # Desempaqueta el turno y la función de la tarea.
            if current_turn >= task_turn:  # Verifica si es el turno adecuado.
                callback()  # Ejecuta la tarea.
                self.scheduled_tasks.remove(task)  # Elimina la tarea de la lista.

    def increment_turn(self) -> None:
        """Incrementa el contador de turnos."""
        self.turn_count += 1  # Incrementa el contador de turnos.

    def handle_enemy_turns(self) -> None:
        """Maneja los turnos de los enemigos y reduce el contador de invisibilidad del jugador."""
        if self.player.invisibility_turns > 0:  # Verifica si el jugador es invisible.
            self.player.invisibility_turns -= 1  # Reduce el contador de invisibilidad.
            if self.player.invisibility_turns == 0:  # Si el contador llega a 0.
                self.message_log.add_message(  # Agrega un mensaje indicando que el jugador es visible.
                    f"{self.player.name} vuelve a ser visible.",
                    color.status_effect_applied,
                )

        for entity in set(self.game_map.actors) - {self.player}:  # Itera sobre los enemigos.
            if entity.ai:  # Verifica si el enemigo tiene inteligencia artificial.
                entity.ai.perform()  # Ejecuta la acción del enemigo.

    def update_fov(self) -> None:
        """Recalcula el área visible basado en la posición del jugador."""
        self.game_map.visible[:] = compute_fov(  # Calcula el campo de visión (FOV).
            self.game_map.tiles["transparent"],  # Usa los tiles transparentes del mapa.
            (self.player.x, self.player.y),  # La posición del jugador.
            radius=8,  # Radio del campo de visión.
        )
        self.game_map.explored |= self.game_map.visible  # Marca como explorado lo visible.

    def render(self, console: Console) -> None:
        """Renderiza la pantalla del juego."""
        self.game_map.render(console)  # Dibuja el mapa del juego.

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)  # Renderiza el registro de mensajes.

        render_functions.render_bar(  # Renderiza la barra de salud del jugador.
            console=console,
            current_value=self.player.fighter.hp,  # Salud actual del jugador.
            maximum_value=self.player.fighter.max_hp,  # Salud máxima del jugador.
            total_width=20,  # Ancho total de la barra.
        )
        render_functions.render_xp_bar(  # Renderiza la barra de experiencia.
            console=console,
            current_xp=self.player.level.current_xp,
            xp_to_next_level=self.player.level.experience_to_next_level,
            total_width=20,
        )

        render_functions.render_dungeon_level(  # Renderiza el nivel del calabozo actual.
            console=console,
            dungeon_level=self.game_world.current_floor,  # Piso actual del juego.
            location=(0, 48),  # Ubicación donde se renderiza el nivel.
        )

    def save_as(self, filename: str) -> None:
        """Guarda el estado del motor del juego en un archivo comprimido, excluyendo el contexto y la consola."""
        context = self.context  # Excluye el contexto temporalmente.
        console = self.console  # Excluye la consola temporalmente.

        self.context = None  # Elimina el contexto del motor.
        self.console = None  # Elimina la consola del motor.

        try:
            save_data = lzma.compress(pickle.dumps(self))  # Serializa y comprime el estado del motor.
            with open(filename, "wb") as f:  # Abre el archivo en modo escritura binaria.
                f.write(save_data)  # Escribe los datos en el archivo.
        finally:
            self.context = context  # Restaura el contexto.
            self.console = console  # Restaura la consola.

    def handle_events(self, events: list[tcod.event.Event]) -> None:
        """Maneja los eventos del juego, incluyendo el guardado al salir."""
        for event in events:  # Itera sobre los eventos.
            if isinstance(event, tcod.event.Quit):  # Verifica si el evento es de tipo Quit.
                if self.player.is_alive:  # Verifica si el jugador está vivo.
                    self.save_as("savegame.sav")  # Guarda la partida automáticamente.
                    self.message_log.add_message("Partida guardada automáticamente al salir.", color.welcome_text)
                raise SystemExit()  # Sale del juego.

class Actor:
    @property
    def is_alive(self) -> bool:
        """El jugador está vivo si tiene puntos de vida positivos."""
        return self.hp > 0  # Verifica si los puntos de vida son mayores a 0.

class Fighter(BaseComponent):
    def die(self) -> None:
        if self.engine.player is self.parent:  # Verifica si el jugador es el que muere.
            original_name = self.parent.name  # Guarda el nombre original del jugador.
            self.engine.last_player_name = original_name  # Asigna el nombre original al atributo.