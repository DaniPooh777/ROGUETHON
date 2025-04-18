from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Callable

import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
import exceptions
from input_handlers import (
    ActionOrHandler,
    AreaRangedAttackHandler,
    SingleRangedAttackHandler,
)

# Importación condicional de clases para comprobación de tipos.
if TYPE_CHECKING:
    from entity import Actor, Item  # Importa las clases Actor e Item solo durante la comprobación de tipos

# Agregar la importación de Actor para evitar el NameError.
from entity import Actor


class Consumable(BaseComponent):
    """Clase base para los ítems consumibles, como pociones o hechizos."""

    parent: Item  # El ítem al que pertenece este componente

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
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),  # Acción que se realiza al elegir un objetivo
        )

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y confunde al objetivo seleccionado."""
        consumer = action.entity  # Actor que usa el consumible
        target = action.target_actor  # Actor objetivo de la confusión

        # Verifica que el objetivo esté en el rango visible
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("No puedes disparar a un lugar que no puedes ver.")
        if not target:
            raise Impossible("Debes seleccionar a un enemigo como objetivo.")
        if target is consumer:
            raise Impossible("No puedes confundirte a ti mismo.")

        # Aplica el efecto de confusión al objetivo
        self.engine.message_log.add_message(
            f"Los ojos de {target.name} parecen distraidos, como empieza a dar tumbos.",
            color.status_effect_applied,
        )
        target.ai = components.ai.ConfusedEnemy(
            entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
        )
        self.consume()  # Consume el ítem después de activarse

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
            radius=self.radius,  # Radio de la explosión
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y lanza una bola de fuego en el área seleccionada."""
        target_xy = action.target_xy

        # Verifica que el lugar objetivo esté visible
        if not self.engine.game_map.visible[target_xy]:
            raise Impossible("No puedes disparar a un lugar que no puedes ver.")

        targets_hit = False  # Bandera que indica si se ha golpeado al menos a un objetivo

        # Recorre todos los actores en el mapa y aplica el daño a los que estén dentro del radio
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    f"{actor.name} se ve envuelto en una gran explosion, recibe {self.damage} de dano."
                )
                actor.fighter.take_damage(self.damage)  # Aplica el daño al actor
                targets_hit = True

        if not targets_hit:
            raise Impossible("No hay objetivos en el radio.")
        self.consume()  # Consume el ítem después de activarse

class HealingConsumable(Consumable):
    """Consumible que recupera una cantidad de salud al consumidor."""

    def __init__(self, amount: int):
        """Inicializa el consumible con la cantidad de salud que recupera."""
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y cura al consumidor."""
        consumer = action.entity  # El consumidor del ítem
        amount_recovered = consumer.fighter.heal(self.amount)  # Recupera la salud

        # Si se ha recuperado salud, muestra un mensaje y consume el ítem
        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"Bebes {self.parent.name}. Has recuperado {amount_recovered} HP.",
                color.health_recovered,
            )
            self.consume()
        else:
            raise Impossible(f"Tienes la vida al maximo.")  # No se puede curar si la salud ya está al máximo

class LightningDamageConsumable(Consumable):
    """Consumible que lanza un rayo causando daño al enemigo más cercano."""

    def __init__(self, damage: int, maximum_range: int):
        """Inicializa el consumible con el daño y el rango máximo del rayo."""
        self.damage = damage
        self.maximum_range = maximum_range

    def activate(self, action: actions.ItemAction) -> None:
        """Activa el consumible y lanza un rayo al enemigo más cercano."""
        consumer = action.entity  # Actor que usa el consumible
        target = None  # Enemigo al que se le lanzará el rayo
        closest_distance = self.maximum_range + 1.0  # Establece una distancia máxima mayor que el rango

        # Busca al enemigo más cercano dentro del rango máximo
        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor  # Establece el objetivo como el enemigo más cercano
                    closest_distance = distance

        # Si se ha encontrado un objetivo, lanza el rayo
        if target:
            self.engine.message_log.add_message(
                f"Un rayo golpea al {target.name} con gran estruendo. Hace {self.damage} de dano."
            )
            target.fighter.take_damage(self.damage)  # Aplica el daño al enemigo
            self.consume()
        else:
            raise Impossible("Ningun enemigo a la vista para atacar.")  # Si no hay enemigo, lanza un error

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

        consumer.invisibility_turns = self.number_of_turns  # Establece los turnos de invisibilidad
        self.engine.message_log.add_message(
            f"{consumer.name} se desvanece en el aire, volviendose invisible durante {self.number_of_turns} turnos.",
            color.status_effect_applied,
        )

        self.consume()