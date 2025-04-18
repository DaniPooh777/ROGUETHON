from __future__ import annotations  # Importación que permite utilizar las anotaciones de tipo en clases antes de ser completamente definidas.

import random  # Importación del módulo random, utilizado para generar movimientos aleatorios.
from typing import List, Optional, Tuple, TYPE_CHECKING  # Importación de tipos para la anotación de tipos.

import numpy as np  # Importación de numpy (utilizado para manipular matrices y realizar cálculos numéricos)
import tcod  # Importación de la librería tcod, utilizada para gráficos y mapas de caminos en juegos roguelike.

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction
import color  # Importación de diferentes tipos de acciones (Acciones para mover, atacar, esperar, etc.)

# Este bloque solo importa las clases cuando se está realizando una verificación de tipos (en tiempo de desarrollo, no en ejecución).
if TYPE_CHECKING:
    from entity import Actor  # Importa la clase `Actor` solo cuando se realiza la comprobación de tipos.
    

class BaseAI(Action):
    """Clase base para la inteligencia artificial (IA) de los enemigos.
    
    Todos los enemigos tendrán una IA que les dictará qué hacer. Esta clase define los métodos generales que serán utilizados
    por las subclases, como la capacidad de calcular un camino hasta un objetivo.
    """
    
    def perform(self) -> None:
        """Método abstracto que debe ser implementado por las subclases.
        
        Define la lógica para realizar una acción que el enemigo puede realizar.
        Cada tipo de IA implementará su propia versión de este método.
        """
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Calcula un camino hacia las coordenadas dadas."""
        cost = np.array(self.engine.game_map.tiles["walkable"], dtype=np.int8)

        for entity in self.engine.game_map.entities:
            if entity.blocks_movement and cost[entity.x, entity.y]:
                cost[entity.x, entity.y] += 10

        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))

        path: List[Tuple[int, int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Verifica que todas las posiciones en el camino sean válidas
        valid_path = [
            (x, y) for x, y in path if self.engine.game_map.in_bounds(x, y) and self.engine.game_map.tiles["walkable"][x, y]
        ]
        return valid_path


class HostileEnemy(BaseAI):
    """IA para enemigos hostiles, que siguen al jugador y lo atacan cuando se acercan.
    
    Esta clase define el comportamiento de un enemigo hostil, que realiza diferentes acciones
    dependiendo de la distancia con el jugador (atacar si está cerca o moverse hacia él si está lejos).
    """

    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []  # Inicializa el atributo path como una lista vacía

    def perform(self) -> None:
        if self.engine.player.invisible:
            return  # Los enemigos no hacen nada si el jugador es invisible

        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            # Calcula un nuevo camino si no hay uno existente
            if not self.path:
                self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)

            # Verifica si el destino es caminable antes de intentar moverse
            if self.engine.game_map.in_bounds(dest_x, dest_y) and self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
                return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    """IA para enemigos confundidos que se mueven aleatoriamente durante un número de turnos.
    
    Cuando un enemigo está confundido, se mueve de manera aleatoria y puede atacar a cualquier entidad que esté en su camino.
    Después de un número determinado de turnos, el enemigo vuelve a su IA original.
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        """Inicializa la IA de un enemigo confundido.
        
        `entity`: La entidad que esta IA controla (un enemigo).
        `previous_ai`: La IA original del enemigo que se restaurará después de que termine la confusión.
        `turns_remaining`: Los turnos restantes durante los cuales el enemigo estará confundido.
        """
        super().__init__(entity)  # Llama al constructor de la clase base.
        self.previous_ai = previous_ai  # Guarda la IA anterior para restaurarla después.
        self.turns_remaining = turns_remaining  # Inicializa los turnos restantes de confusión.

    def perform(self) -> None:
        """Realiza la acción de un enemigo confundido en su turno.
        
        Si el enemigo ya no está confundido, vuelve a su IA original. Si aún está confundido, se mueve aleatoriamente.
        """
        if self.turns_remaining <= 0:
            # Si ya no quedan turnos de confusión, restaura la IA original del enemigo.
            self.engine.message_log.add_message(
                f"{self.entity.name} ya no esta confundido.",
            )
            self.entity.ai = self.previous_ai
        else:
            # Si aún queda confusión, el enemigo se mueve de manera aleatoria en una dirección.
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Noroeste
                    (0, -1),   # Norte
                    (1, -1),   # Noreste
                    (-1, 0),   # Oeste
                    (1, 0),    # Este
                    (-1, 1),   # Suroeste
                    (0, 1),    # Sur
                    (1, 1),    # Sureste
                ]
            )

            self.turns_remaining -= 1  # Decrementa los turnos de confusión.

            # El enemigo intenta moverse en la dirección aleatoria elegida o atacar si hay una entidad en esa dirección.
            return BumpAction(self.entity, direction_x, direction_y).perform()


class RangedEnemy(BaseAI):
    """IA para enemigos que atacan a distancia, como el goblin."""

    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.turns_to_attack = 3  # El goblin ataca cada 3 turnos.

    def perform(self) -> None:
        """Realiza la acción del goblin en su turno."""
        target = self.engine.player  # El objetivo es el jugador.
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Distancia de Chebyshev.

        # Verifica si el goblin está dentro del campo de visión del jugador.
        if not self.engine.game_map.visible[self.entity.x, self.entity.y]:
            return WaitAction(self.entity).perform()  # Espera si no está visible.

        if distance <= 5:  # Si el jugador está dentro del rango de ataque.
            if self.turns_to_attack <= 0:
                # Ataca al jugador si es el turno de atacar.
                self.engine.message_log.add_message(
                    f"{self.entity.name} lanza un ataque a distancia contra {target.name}.",
                    color.enemy_atk,
                )
                target.fighter.take_damage(4)  # Hace 4 puntos de daño.
                self.turns_to_attack = 3  # Reinicia el contador de turnos.
            else:
                self.turns_to_attack -= 1  # Reduce el contador de turnos.
            return  # No se mueve si está dentro del rango.

        # Si el jugador está fuera del rango, se mueve hacia él.
        self.path = self.get_path_to(target.x, target.y)
        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

        return WaitAction(self.entity).perform()  # Espera si no puede moverse.
