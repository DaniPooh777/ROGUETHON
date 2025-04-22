"""
Este código define una serie de clases de objetos consumibles en un juego de rol basado en turnos.
Los consumibles pueden ser utilizados por actores del juego (como el jugador o enemigos) para activar efectos
que afectan el estado de los actores en el juego. Los efectos incluyen confusión, daño, curación, invisibilidad
y aumentos temporales a la defensa. Cada tipo de consumible extiende la clase base `Consumable` y define su comportamiento
cuando se activa, gestionando la interacción entre los actores, el consumo del ítem y el efecto aplicado.
"""

from __future__ import annotations  # Permite la anotación de tipos para clases que se definen después en el código.
from typing import Optional, TYPE_CHECKING, Callable  # Importa herramientas para el manejo de tipos en el código.
from components.base_component import BaseComponent  # Importa la clase base para los componentes de los ítems.
from exceptions import Impossible  # Importa la excepción personalizada "Impossible".
from entity import Actor  # Importa la clase Actor, que representa a los personajes en el juego.

import actions  # Importa las acciones que los actores pueden realizar.
import color  # Importa los colores utilizados en la interfaz gráfica o mensajes.
import components.ai  # Importa componentes relacionados con la inteligencia artificial de los actores.
import components.inventory  # Importa componentes relacionados con el inventario de los actores.
import exceptions  # Importa las excepciones personalizadas.

from input_handlers import (  # Importa los manejadores de entrada de acciones y ataques.
    ActionOrHandler,  # Importa el manejador que puede ser una acción o un controlador de entrada.
    AreaRangedAttackHandler,  # Importa el manejador para ataques a distancia en área.
    SingleRangedAttackHandler,  # Importa el manejador para ataques a distancia individuales.
)

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from entity import Actor, Item  # Importa las clases Actor e Item solo para la comprobación de tipos.

class Consumable(BaseComponent):
    """Clase base para los ítems consumibles, como pociones o hechizos."""

    parent: Item  # El ítem al que pertenece este componente.

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Devuelve la acción que este ítem puede realizar cuando se usa."""
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """Método abstracto que debe ser implementado por cada consumible para definir qué hace al activarse."""
        raise NotImplementedError()

    def consume(self) -> None:
        """Elimina el item consumido de su inventario."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)  # Elimina el ítem del inventario

class ConfusionConsumable(Consumable):
    """Consumible que confunde a un enemigo durante un número de turnos."""

    def __init__(self, number_of_turns: int):
        """Inicializa el consumible con el número de turnos de confusión."""
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        """Devuelve la acción de atacar a un objetivo con este consumible."""
        self.engine.message_log.add_message(
            "Seleccione un objetivo.", color.needs_target
        )
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),  # Acción que se realiza al elegir un objetivo.
        )

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y confunde al objetivo seleccionado."""
        consumer = action.entity  # Actor que usa el consumible.
        target = action.target_actor  # Actor objetivo de la confusión.

        # Verifica que el objetivo esté en el rango visible.
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("No puedes disparar a un lugar que no puedes ver.")
        if not target:
            raise Impossible("Debes seleccionar a un enemigo como objetivo.")
        if target is consumer:
            raise Impossible("No puedes confundirte a ti mismo.")

        # Aplica el efecto de confusión al objetivo.
        self.engine.message_log.add_message(
            f"Los ojos de {target.name} parecen distraidos, como empieza a dar tumbos.",
            color.status_effect_applied,
        )
        target.ai = components.ai.ConfusedEnemy(
            entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
        )
        self.consume()  # Consume el ítem después de activarse.

class FireballDamageConsumable(Consumable):
    """Consumible que lanza una bola de fuego causando daño en un área."""

    def __init__(self, damage: int, radius: int):
        """Inicializa el consumible con el daño y el radio de efecto."""
        self.damage = damage
        self.radius = radius

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        """Devuelve la acción de lanzar un área de ataque con este consumible."""
        self.engine.message_log.add_message(
            "Seleccione un objetivo.", color.needs_target
        )
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,  # Radio de la explosión.
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y lanza una bola de fuego en el área seleccionada."""
        target_xy = action.target_xy

        # Verifica que el lugar objetivo esté visible.
        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("No puedes disparar a un lugar que no puedes ver.")

        targets_hit = False  # Bandera que indica si se ha golpeado al menos a un objetivo.

        # Recorre todos los actores en el mapa y aplica el daño a los que estén dentro del radio.
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"{actor.name} se ve envuelto en una gran explosion, recibe {self.damage} de dano."
                )
                actor.fighter.take_damage(self.damage)  # Aplica el daño al actor.
                targets_hit = True

        if not targets_hit:
            raise Impossible("No hay objetivos en el radio.")
        self.consume()  # Consume el ítem después de activarse.

class HealingConsumable(Consumable):
    """Consumible que recupera una cantidad de salud al consumidor."""

    def __init__(self, amount: int):
        """Inicializa el consumible con la cantidad de salud que recupera."""
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y cura al consumidor."""
        consumer = action.entity

        if consumer.fighter.hp == consumer.fighter.max_hp:
            raise exceptions.Impossible("Tienes la vida al maximo.")

        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"Recuperaste {amount_recovered} puntos de vida.", color.health_recovered
            )
        else:
            self.engine.message_log.add_message(
                "No puedes recuperar más salud.", color.impossible
            )

        self.consume()

class LightningDamageConsumable(Consumable):
    """Consumible que lanza un rayo causando daño al enemigo más cercano."""

    def __init__(self, damage: int, maximum_range: int):
        """Inicializa el consumible con el daño y el rango máximo del rayo."""
        self.damage = damage
        self.maximum_range = maximum_range

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y lanza un rayo al enemigo más cercano."""
        consumer = action.entity  # Actor que usa el consumible.
        target = None  # Enemigo al que se le lanzará el rayo.
        closest_distance = self.maximum_range + 1.0  # Establece una distancia máxima mayor que el rango.

        # Busca al enemigo más cercano dentro del rango máximo.
        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor  # Establece el objetivo como el enemigo más cercano.
                    closest_distance = distance

        # Si se ha encontrado un objetivo, lanza el rayo.
        if target:
            self.engine.message_log.add_message(
                f"Un rayo golpea al {target.name} con gran estruendo. Hace {self.damage} de dano."
            )
            target.fighter.take_damage(self.damage)  # Aplica el daño al enemigo.
            self.consume()
        else:
            raise Impossible("Ningun enemigo a la vista para atacar.")  # Si no hay enemigo, lanza un error.

class DefensiveScrollConsumable(Consumable):
    """Consumible que aumenta la defensa del jugador durante un número de turnos."""

    def __init__(self, defense_bonus: int, number_of_turns: int):
        self.defense_bonus = defense_bonus
        self.number_of_turns = number_of_turns

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.entity  # Aseguramos que consumer sea el actor que usa el ítem.

        if not isinstance(consumer, Actor):  # Validamos que sea un Actor.
            raise exceptions.Impossible("Solo el jugador puede usar este pergamino.")

        # Aumenta la defensa del jugador temporalmente.
        consumer.fighter.activate_defense_bonus(self.defense_bonus, self.number_of_turns)
        self.consume()

        self.engine.message_log.add_message(
            f"{consumer.name} siente su piel endurecerse, ganando {self.defense_bonus} puntos de defensa durante {self.number_of_turns} turnos.",
            color.status_effect_applied,
        )

class InvisibilityScrollConsumable(Consumable):
    """Consumible que hace al jugador invisible durante un número de turnos."""

    def __init__(self, number_of_turns: int):
        """Inicializa el consumible con el número de turnos de invisibilidad."""
        self.number_of_turns = number_of_turns

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y hace al jugador invisible."""
        consumer = action.entity

        if not isinstance(consumer, Actor):
            raise exceptions.Impossible("Solo el jugador puede usar este pergamino.")

        consumer.invisibility_turns = self.number_of_turns  # Establece los turnos de invisibilidad.
        self.engine.message_log.add_message(
            f"{consumer.name} se desvanece en el aire, volviendose invisible durante {self.number_of_turns} turnos.",
            color.status_effect_applied,
        )

        self.consume()