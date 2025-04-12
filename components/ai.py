from __future__ import annotations  # Importación que permite utilizar las anotaciones de tipo en clases antes de ser completamente definidas.

import random  # Importación del módulo random, utilizado para generar movimientos aleatorios.
from typing import List, Optional, Tuple, TYPE_CHECKING  # Importación de tipos para la anotación de tipos.

import numpy as np  # Importación de numpy (utilizado para manipular matrices y realizar cálculos numéricos)
import tcod  # Importación de la librería tcod, utilizada para gráficos y mapas de caminos en juegos roguelike.

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction  # Importación de diferentes tipos de acciones (Acciones para mover, atacar, esperar, etc.)

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
        """Calcula y retorna un camino hasta la posición destino.
        
        Utiliza un algoritmo de búsqueda de caminos para encontrar la mejor ruta hasta el destino.
        
        Si no hay un camino válido, retorna una lista vacía.
        """
        # Copia el array de walkable (camino transitable) del mapa de juego.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        # Recorre todas las entidades en el mapa para verificar si bloquean el movimiento.
        for entity in self.entity.gamemap.entities:
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Incrementa el costo de las posiciones bloqueadas para evitar que los enemigos se muevan allí.
                # Un número más bajo hace que los enemigos se agrupen más en pasillos. Un número más alto les hará tomar rutas más largas.
                cost[entity.x, entity.y] += 10

        # Crea un gráfico basado en el array de costos y lo pasa al buscador de caminos.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Añade la posición inicial como raíz.

        # Calcula el camino hasta el destino y elimina la posición inicial del camino.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convierte el resultado de la ruta de List[List[int]] a List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
    """IA para enemigos hostiles, que siguen al jugador y lo atacan cuando se acercan.
    
    Esta clase define el comportamiento de un enemigo hostil, que realiza diferentes acciones
    dependiendo de la distancia con el jugador (atacar si está cerca o moverse hacia él si está lejos).
    """

    def __init__(self, entity: Actor):
        """Inicializa la IA de un enemigo hostil, asignándole la entidad a la que está asociada.
        
        `entity`: La entidad que esta IA controla (un enemigo).
        """
        super().__init__(entity)  # Llama al constructor de la clase base.
        self.path: List[Tuple[int, int]] = []  # Inicializa la lista que contiene el camino hacia el jugador.

    def perform(self) -> None:
        """Realiza la acción que el enemigo debe realizar en su turno.
        
        El enemigo hostil se moverá hacia el jugador si está lejos o atacará si está cerca.
        """
        target = self.engine.player  # El objetivo es el jugador.
        dx = target.x - self.entity.x  # Calcula la diferencia en la posición horizontal entre el enemigo y el jugador.
        dy = target.y - self.entity.y  # Calcula la diferencia en la posición vertical entre el enemigo y el jugador.
        distance = max(abs(dx), abs(dy))  # Calcula la distancia usando la distancia de Chebyshev.

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:  # Verifica si el enemigo puede ver su posición actual.
            if distance <= 1:
                # Si el jugador está a distancia de ataque, realiza un ataque cuerpo a cuerpo.
                return MeleeAction(self.entity, dx, dy).perform()

            # Si el jugador está lejos, calcula el camino hacia el jugador.
            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            # Si hay un camino, mueve al enemigo hacia el siguiente punto del camino.
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

        # Si no hay camino, espera.
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
                f"{self.entity.name} ya no está confundido.",
            )
            self.entity.ai = self.previous_ai
        else:
            # Si aún queda confusión, el enemigo se mueve aleatoriamente en una dirección.
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
