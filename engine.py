# Importación de módulos necesarios
from __future__ import annotations  # Permite la anotación de tipos con clases que aún no están definidas.

import lzma  # Importa el módulo lzma para la compresión de datos.
import pickle  # Importa el módulo pickle para la serialización de objetos.
from typing import TYPE_CHECKING, Callable  # Importa TYPE_CHECKING para la comprobación de tipos en tiempo de desarrollo.

from tcod.console import Console  # Importa la clase Console de la biblioteca tcod para la salida gráfica.
from tcod.map import compute_fov  # Importa compute_fov para calcular el campo de visión (FOV).
import tcod  # Importa la biblioteca tcod para gráficos y operaciones relacionadas con el juego.
import tcod.event  # Asegúrate de que tcod.event esté importado

import color
from components.base_component import BaseComponent
import exceptions  # Importa las excepciones personalizadas.
from message_log import MessageLog  # Importa el sistema de registro de mensajes.
import render_functions  # Importa funciones de renderizado personalizadas.

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
        self.mouse_location = (0, 0)  # Inicializa la ubicación del ratón.
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
        current_turn = self.turn_count
        for task in list(self.scheduled_tasks):
            task_turn, callback = task
            if current_turn >= task_turn:
                callback()  # Ejecuta la tarea
                self.scheduled_tasks.remove(task)

    def increment_turn(self) -> None:
        """Incrementa el contador de turnos."""
        self.turn_count += 1

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

    def update_fov(self) -> None:
        """Recalcula el área visible basado en la posición del jugador."""
        # Calcula el campo de visión (FOV) a partir del mapa de tiles "transparentes".
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),  # La posición del jugador.
            radius=8,  # Radio del campo de visión.
        )
        # Marca como "explorado" todo lo que esté dentro del campo de visión.
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        """Renderiza la pantalla del juego."""
        self.game_map.render(console)  # Dibuja el mapa del juego.

        # Renderiza el registro de mensajes en la pantalla.
        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        # Renderiza la barra de salud del jugador.
        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,  # Salud actual del jugador.
            maximum_value=self.player.fighter.max_hp,  # Salud máxima del jugador.
            total_width=20,  # Ancho total de la barra.
        )

        # Renderiza el nivel del calabozo actual (piso actual).
        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,  # Piso actual del juego.
            location=(0, 47),  # Ubicación donde se renderiza el nivel.
        )

        # Renderiza el nombre de la entidad bajo el cursor del ratón.
        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    def save_as(self, filename: str) -> None:
        """Guarda el estado del motor del juego en un archivo comprimido, excluyendo el contexto y la consola."""
        context = self.context  # Excluye el contexto temporalmente.
        console = self.console  # Excluye la consola temporalmente.
        
        self.context = None
        self.console = None

        try:
            save_data = lzma.compress(pickle.dumps(self))  # Serializa y comprime el estado del motor.
            with open(filename, "wb") as f:
                f.write(save_data)  # Escribe los datos en el archivo.
        finally:
            self.context = context  # Restaura el contexto.
            self.console = console  # Restaura la consola.

    def handle_events(self, events: list[tcod.event.Event]) -> None:
        """Maneja los eventos del juego, incluyendo el guardado al salir."""
        for event in events:
            if isinstance(event, tcod.event.Quit):
                if self.player.is_alive:
                    self.save_as("savegame.sav")  # Guarda la partida automáticamente.
                    self.message_log.add_message("Partida guardada automáticamente al salir.", color.welcome_text)
                raise SystemExit()
            # ...existing event handling code...

class Actor:
    @property
    def is_alive(self) -> bool:
        """El jugador está vivo si tiene puntos de vida positivos."""
        return self.hp > 0  # Asegúrate de que esto no dependa de la IA o el estado de invisibilidad.

class Fighter(BaseComponent):
    def die(self) -> None:
        if self.engine.player is self.parent:
            original_name = self.parent.name  # Guarda el nombre original del jugador
            self.engine.last_player_name = original_name  # Asigna el nombre original al atributo
        # ...existing code...