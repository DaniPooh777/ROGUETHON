"""
Propósito del código:
Este fragmento de código implementa diferentes tipos de inteligencia artificial (IA) para los enemigos en un juego estilo roguelike.
Cada clase de IA extiende la clase `BaseAI` y define comportamientos específicos para los enemigos, como moverse hacia el jugador, 
atacar, o moverse aleatoriamente si están confundidos.
"""

from __future__ import annotations  # Permite usar anotaciones de tipo en clases antes de su definición completa.
from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction  # Importa diferentes acciones para el juego.
from typing import List, Optional, Tuple, TYPE_CHECKING  # Importa tipos para la anotación de tipos, útil para control de tipos en las funciones.

import numpy as np  # Importa numpy para manipular matrices y realizar cálculos numéricos (como los mapas de caminos).
import tcod  # Importa tcod, la librería usada para gráficos en juegos roguelike y mapas de caminos.
import random  # Importa el módulo random para generar números aleatorios, utilizado para movimientos aleatorios.
import color  # Importa un módulo que contiene colores predefinidos para mensajes en el juego.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from entity import Actor  # Solo importa la clase `Actor` durante la comprobación de tipos.

class BaseAI(Action):
    """
    Clase base para la inteligencia artificial (IA) de los enemigos.
    Define los métodos generales que las subclases de enemigos usarán, como calcular caminos hacia el jugador.
    """
    
    def perform(self) -> None:
        """
        Método abstracto que debe ser implementado por las subclases.
        Define lo que la IA de cada enemigo debe hacer durante su turno.
        """
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Calcula un camino desde la posición del enemigo hasta las coordenadas de destino."""
        cost = np.array(self.engine.game_map.tiles["walkable"], dtype=np.int8)  # Crea una matriz de costos (el esfuerzo necesario para moverse) para el mapa.

        # Modifica los costos de las casillas bloqueadas para hacerlas más costosas de atravesar.
        for entity in self.engine.game_map.entities:
            if entity.blocks_movement and cost[entity.x, entity.y]:
                cost[entity.x, entity.y] += 10

        # Crea un gráfico con los costos y utiliza el algoritmo Pathfinder de tcod para calcular el camino.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((self.entity.x, self.entity.y))

        # Calcula el camino hacia el destino.
        path: List[Tuple[int, int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Filtra el camino para asegurarse de que todas las posiciones son válidas.
        valid_path = [
            (x, y) for x, y in path if self.engine.game_map.in_bounds(x, y) and self.engine.game_map.tiles["walkable"][x, y]
        ]
        return valid_path

class HostileEnemy(BaseAI):
    """IA para enemigos hostiles que siguen al jugador y lo atacan cuando se acercan."""

    def __init__(self, entity: Actor):
        super().__init__(entity)  # Inicializa la clase base con la entidad.
        self.path: List[Tuple[int, int]] = []  # Inicializa el atributo path (camino) como una lista vacía.

    def perform(self) -> None:
        if self.engine.player.invisible:
            return  # Si el jugador es invisible, el enemigo no hace nada.

        target = self.engine.player  # El objetivo del enemigo es el jugador.
        dx = target.x - self.entity.x  # Calcula la diferencia en las coordenadas x.
        dy = target.y - self.entity.y  # Calcula la diferencia en las coordenadas y.
        distance = max(abs(dx), abs(dy))  # Calcula la distancia de Chebyshev (máxima diferencia entre las coordenadas).

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:  # Si el enemigo está cerca del jugador (distancia 1).
                return MeleeAction(self.entity, dx, dy).perform()  # Realiza un ataque cuerpo a cuerpo.

            # Si no hay un camino, calcula uno nuevo hacia el jugador.
            if not self.path:
                self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)  # Obtiene el siguiente destino en el camino.

            # Verifica que el destino sea válido y caminable.
            if self.engine.game_map.in_bounds(dest_x, dest_y) and self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
                return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()  # Mueve al enemigo.

        return WaitAction(self.entity).perform()  # Si no puede moverse, espera.

class ConfusedEnemy(BaseAI):
    """IA para enemigos confundidos que se mueven aleatoriamente durante varios turnos."""

    def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int):
        """Inicializa la IA para un enemigo confundido."""
        super().__init__(entity)  # Llama al constructor de la clase base.
        self.previous_ai = previous_ai  # Guarda la IA anterior para restaurarla después.
        self.turns_remaining = turns_remaining  # Número de turnos restantes de confusión.

    def perform(self) -> None:
        """Realiza la acción del enemigo confundido durante su turno."""
        if self.turns_remaining <= 0:
            # Si ya no quedan turnos de confusión, restaura la IA original del enemigo.
            self.engine.message_log.add_message(f"{self.entity.name} ya no esta confundido.")
            self.entity.ai = self.previous_ai
        else:
            # Si aún queda confusión, el enemigo se mueve aleatoriamente.
            direction_x, direction_y = random.choice(
                [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
            )

            self.turns_remaining -= 1  # Decrementa los turnos de confusión.

            # Realiza un movimiento aleatorio.
            return BumpAction(self.entity, direction_x, direction_y).perform()

class RangedEnemy(BaseAI):
    """IA para enemigos que atacan a distancia, como un goblin."""

    def __init__(self, entity: Actor):
        super().__init__(entity)  # Inicializa la clase base.
        self.turns_to_attack = 3  # El goblin ataca cada 3 turnos.

    def perform(self) -> None:
        """Realiza la acción del goblin en su turno."""
        target = self.engine.player  # El objetivo es el jugador.
        # Si el jugador es invisible, el goblin no hace nada.
        if target.invisible:
            return WaitAction(self.entity).perform()
        dx = target.x - self.entity.x  # Calcula la diferencia en las coordenadas x.
        dy = target.y - self.entity.y  # Calcula la diferencia en las coordenadas y.
        distance = max(abs(dx), abs(dy))  # Calcula la distancia de Chebyshev.

        if not self.engine.game_map.visible[self.entity.x, self.entity.y]:
            return WaitAction(self.entity).perform()  # Espera si el goblin no está en la vista del jugador.

        if distance <= 5:  # Si el jugador está dentro del rango de ataque a distancia.
            if self.turns_to_attack <= 0:
                # Ataca al jugador si es el turno de atacar.
                damage = 4  # Define el daño que inflige el ataque a distancia.
                self.engine.message_log.add_message(
                    f"{self.entity.name} dispara una flecha a {target.name}. Hace {damage} puntos de dano.", color.enemy_atk
                )
                target.fighter.take_damage(4)  # El goblin hace 4 puntos de daño al jugador.
                self.turns_to_attack = 3  # Reinicia el contador de turnos de ataque.
            else:
                self.turns_to_attack -= 1  # Reduce el contador de turnos de ataque.
            return  # No se mueve si está dentro del rango de ataque.

        # Si el jugador está fuera del rango, se mueve hacia él.
        self.path = self.get_path_to(target.x, target.y)
        if self.path:
            dest_x, dest_y = self.path.pop(0)  # Obtiene el siguiente destino en el camino.
            return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()  # Mueve al goblin.

        return WaitAction(self.entity).perform()  # Si no puede moverse, espera.