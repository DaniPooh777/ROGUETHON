"""
Propósito del código:
Este fragmento de código implementa diferentes tipos de inteligencia artificial (IA) para los enemigos en un juego estilo roguelike.
Cada clase de IA extiende la clase `BaseAI` y define comportamientos específicos para los enemigos, como moverse hacia el jugador,
atacar, o moverse aleatoriamente si están confundidos.
"""

from __future__ import (
    annotations,
)  # Permite usar anotaciones de tipo en clases antes de su definición completa.
from systems.actions import (
    Action,
    BumpAction,
    MeleeAction,
    MovementAction,
    WaitAction,
)  # Importa diferentes acciones para el juego.
from typing import (
    List,
    Optional,
    Tuple,
    TYPE_CHECKING,
)  # Importa tipos para la anotación de tipos, útil para control de tipos en las funciones.

import numpy as np  # Importa numpy para manipular matrices y realizar cálculos numéricos (como los mapas de caminos).
import tcod  # Importa tcod, la librería usada para gráficos en juegos roguelike y mapas de caminos.
import random  # Importa el módulo random para generar números aleatorios, utilizado para movimientos aleatorios.
from ui import (
    colors as color,
)  # Importa un módulo que contiene colores predefinidos para mensajes en el juego.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from entities.entity import (
        Actor,
    )  # Solo importa la clase `Actor` durante la comprobación de tipos.


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
        cost = np.array(
            self.engine.game_map.tiles["walkable"], dtype=np.int8
        )  # Crea una matriz de costos (el esfuerzo necesario para moverse) para el mapa.

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
            (x, y)
            for x, y in path
            if self.engine.game_map.in_bounds(x, y)
            and self.engine.game_map.tiles["walkable"][x, y]
        ]
        return valid_path


class HostileEnemy(BaseAI):
    """IA para enemigos hostiles que siguen al jugador y lo atacan cuando se acercan."""

    def __init__(self, entity: Actor):
        super().__init__(entity)  # Inicializa la clase base con la entidad.
        self.path: List[
            Tuple[int, int]
        ] = []  # Inicializa el atributo path (camino) como una lista vacía.
        # Posición inicial para retorno
        self.initial_x = entity.x
        self.initial_y = entity.y
        # Turnos sin ver al jugador
        self.turns_without_target = 0
        # Rango de búsqueda por defecto
        self.search_range = 10
        # Threshold de miedo (50% HP)
        self.fear_threshold = 0.5
        # Turnos de fear (para huir lento cada 2 turnos)
        self.fear_turns = 0

    def perform(self) -> None:
        if self.engine.player.invisible:
            self.turns_without_target += 1
            return  # Si el jugador es invisible, el enemigo no hace nada.

        target = self.engine.player  # El objetivo del enemigo es el jugador.
        dx = target.x - self.entity.x  # Calcula la diferencia en las coordenadas x.
        dy = target.y - self.entity.y  # Calcula la diferencia en las coordenadas y.
        distance = max(
            abs(dx), abs(dy)
        )  # Calcula la distancia de Chebyshev (máxima diferencia entre las coordenadas).

        # Verificar si ve al jugador
        sees_player = self.engine.game_map.visible[self.entity.x, self.entity.y]
        
        if sees_player:
            self.turns_without_target = 0
        else:
            self.turns_without_target += 1

        # Ver estado de HP para fear response
        max_hp = self.entity.fighter.max_hp
        current_hp = self.entity.fighter.hp
        hp_ratio = current_hp / max_hp if max_hp > 0 else 1.0
        
        # Si tiene miedo (baja HP), huir siempre
        if hp_ratio < self.fear_threshold:
            # Intentar huir cada turno (más visible)
            return self._fleeing_from_player()
        
        # Timeout: si no encuentra al jugador por X turnos, volver a posición inicial
        if self.turns_without_target >= self.search_range:
            return self._return_to_initial()
        
        # Si ve al jugador o lo persiguió recentemente
        if self.turns_without_target < self.search_range:
            if sees_player or distance <= self.search_range:
                # Solo ataca si es orthogonal (no diagonal)
                is_orthogonal = (dx == 0) != (dy == 0)
                
                if distance == 1 and is_orthogonal:
                    return MeleeAction(
                        self.entity, dx, dy
                    ).perform()  # Realiza un ataque cuerpo a cuerpo.

                # Si VE al jugador: recalcula el camino cada turno hacia donde ESTA ahora.
                # Si NO lo ve pero esta en rango: solo calcula si no hay camino (persecucion a ciegas).
                if sees_player:
                    self.path = self.get_path_to(target.x, target.y)
                elif not self.path:
                    self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(
                0
            )  # Obtiene el siguiente destino en el camino.

            # Verifica que el destino sea válido y caminable.
            if (
                self.engine.game_map.in_bounds(dest_x, dest_y)
                and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
            ):
                return MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y
                ).perform()  # Mueve al enemigo.

        return WaitAction(self.entity).perform()  # Si no puede moverse, espera.

    def _fleeing_from_player(self) -> None:
        """Huye en dirección opuesta al jugador."""
        target = self.engine.player
        dx = self.entity.x - target.x  # Dirección opuesta
        dy = self.entity.y - target.y
        
        # Normalizar a -1, 0, o 1
        dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        # Intentar mover en dirección opuesta
        dest_x = self.entity.x + dx
        dest_y = self.entity.y + dy
        
        if (
            self.engine.game_map.in_bounds(dest_x, dest_y)
            and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
            and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        ):
            return MovementAction(self.entity, dx, dy).perform()
        
        # Si está bloqueado, intentar direcciones alternativas
        for alt_dx, alt_dy in [(0, dy), (dx, 0), (-dx, -dy), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            if alt_dx == 0 and alt_dy == 0:
                continue
            dest_x = self.entity.x + alt_dx
            dest_y = self.entity.y + alt_dy
            if (
                self.engine.game_map.in_bounds(dest_x, dest_y)
                and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
                and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
            ):
                return MovementAction(self.entity, alt_dx, alt_dy).perform()
        
        # Si no puede moverse, esperar
        return WaitAction(self.entity).perform()
    
    def _return_to_initial(self) -> None:
        if self.entity.x == self.initial_x and self.entity.y == self.initial_y:
            self.turns_without_target = 0
            return WaitAction(self.entity).perform()
        
        if not self.path:
            self.path = self.get_path_to(self.initial_x, self.initial_y)
        
        if self.path:
            dest_x, dest_y = self.path.pop(0)
            if (
                self.engine.game_map.in_bounds(dest_x, dest_y)
                and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
            ):
                return MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y
                ).perform()
        
        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    """IA para enemigos confundidos que se mueven aleatoriamente durante varios turnos."""

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        """Inicializa la IA para un enemigo confundido."""
        super().__init__(entity)  # Llama al constructor de la clase base.
        self.previous_ai = (
            previous_ai  # Guarda la IA anterior para restaurarla después.
        )
        self.turns_remaining = (
            turns_remaining  # Número de turnos restantes de confusión.
        )

    def perform(self) -> None:
        """Realiza la acción del enemigo confundido durante su turno."""
        if self.turns_remaining <= 0:
            # Si ya no quedan turnos de confusión, restaura la IA original del enemigo.
            self.engine.message_log.add_message(
                f"{self.entity.name} ya no esta confundido."
            )
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
        self.path: List[Tuple[int, int]] = []
        # Posición inicial para retorno
        self.initial_x = entity.x
        self.initial_y = entity.y
        # Turnos sin ver al jugador
        self.turns_without_target = 0
        # Rango de búsqueda por defecto
        self.search_range = 8
        # Threshold de miedo (50% HP)
        self.fear_threshold = 0.5
        # Turnos de fear (para huir lento cada 2 turnos)
        self.fear_turns = 0

    def perform(self) -> None:
        """Realiza la acción del goblin en su turno."""
        target = self.engine.player  # El objetivo es el jugador.
        # Si el jugador es invisible, el goblin no hace nada.
        if target.invisible:
            self.turns_without_target += 1
            return WaitAction(self.entity).perform()
        
        dx = target.x - self.entity.x  # Calcula la diferencia en las coordenadas x.
        dy = target.y - self.entity.y  # Calcula la diferencia en las coordenadas y.
        distance = max(abs(dx), abs(dy))  # Calcula la distancia de Chebyshev.

        # Verificar si ve al jugador
        sees_player = self.engine.game_map.visible[self.entity.x, self.entity.y]
        
        if sees_player:
            self.turns_without_target = 0
        else:
            self.turns_without_target += 1

        # Ver estado de HP para fear response
        max_hp = self.entity.fighter.max_hp
        current_hp = self.entity.fighter.hp
        hp_ratio = current_hp / max_hp if max_hp > 0 else 1.0
        
        # Si tiene miedo (baja HP), huir siempre
        if hp_ratio < self.fear_threshold:
            return self._fleeing_from_player()
        
        # Timeout: si no encuentra al jugador por X turnos, volver a posición inicial
        if self.turns_without_target >= self.search_range:
            return self._return_to_initial()
        
        # Solo ataca a distancia si es orthogonal (no diagonal)
        is_orthogonal = (dx == 0) != (dy == 0)
        
        if sees_player and distance <= 5 and is_orthogonal:
            if self.turns_to_attack <= 0:
                # Ataca al jugador si es el turno de atacar.
                damage = 4  # Define el daño que inflige el ataque a distancia.
                self.engine.message_log.add_message(
                    f"{self.entity.name} dispara una flecha a {target.name}. Hace {damage} puntos de dano.",
                    color.enemy_atk,
                )
                target.fighter.take_damage(4)  # El goblin hace 4 puntos de daño al jugador.
                self.turns_to_attack = 3  # Reinicia el contador de turnos de ataque.
            else:
                self.turns_to_attack -= 1  # Reduce el contador de turnos de ataque.
            return  # No se mueve si está dentro del rango de ataque.

        # Si está muy lejos o no ve al jugador, perseguir/moverse
        if not sees_player and self.turns_without_target < self.search_range:
            # Intentar acercarse
            self.path = self.get_path_to(target.x, target.y)
            if self.path:
                dest_x, dest_y = self.path.pop(0)
                return MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y
                ).perform()  # Mueve al goblin.

        return WaitAction(self.entity).perform()  # Si no puede moverse, espera.

    def _fleeing_from_player(self) -> None:
        """Huye en dirección opuesta al jugador."""
        target = self.engine.player
        dx = self.entity.x - target.x
        dy = self.entity.y - target.y
        
        dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        dest_x = self.entity.x + dx
        dest_y = self.entity.y + dy
        
        if (
            self.engine.game_map.in_bounds(dest_x, dest_y)
            and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
            and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        ):
            return MovementAction(self.entity, dx, dy).perform()
        
        for alt_dx, alt_dy in [(0, dy), (dx, 0), (-dx, -dy), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            if alt_dx == 0 and alt_dy == 0:
                continue
            dest_x = self.entity.x + alt_dx
            dest_y = self.entity.y + alt_dy
            if (
                self.engine.game_map.in_bounds(dest_x, dest_y)
                and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
                and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
            ):
                return MovementAction(self.entity, alt_dx, alt_dy).perform()
        
        return WaitAction(self.entity).perform()

def _return_to_initial(self) -> None:
        """Huye en dirección opuesta al jugador."""
        target = self.engine.player
        dx = self.entity.x - target.x  # Dirección opuesta
        dy = self.entity.y - target.y
        
        # Normalizar a -1, 0, o 1
        dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        # Intentar mover en dirección opuesta
        dest_x = self.entity.x + dx
        dest_y = self.entity.y + dy
        
        if (
            self.engine.game_map.in_bounds(dest_x, dest_y)
            and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
            and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        ):
            return MovementAction(self.entity, dx, dy).perform()
        
        # Si está bloqueado, intentar direcciones alternativas
        for alt_dx, alt_dy in [(0, dy), (dx, 0), (-dx, -dy), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            if alt_dx == 0 and alt_dy == 0:
                continue
            dest_x = self.entity.x + alt_dx
            dest_y = self.entity.y + alt_dy
            if (
                self.engine.game_map.in_bounds(dest_x, dest_y)
                and self.engine.game_map.tiles["walkable"][dest_x, dest_y]
                and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
            ):
                return MovementAction(self.entity, alt_dx, alt_dy).perform()
        
        # Si no puede moverse, esperar
        return WaitAction(self.entity).perform()
