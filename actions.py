from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

# Importación condicional para las clases de la Engine y los actores solo en tiempo de comprobación de tipos
if TYPE_CHECKING:
    from engine import Engine  # La clase Engine, que maneja la lógica del juego
    from entity import Actor, Entity, Item  # Clases Actor, Entity y Item para las entidades del juego


class Action:
    """Acción base que se realiza en el juego. Las acciones específicas como mover o atacar heredan de esta clase."""

    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity  # La entidad que realiza la acción (por ejemplo, el jugador o un enemigo)

    @property
    def engine(self) -> Engine:
        """Devuelve el motor (Engine) al que pertenece esta acción."""
        return self.entity.gamemap.engine  # Obtiene el motor desde el mapa de la entidad

    def perform(self) -> None:
        """Realiza la acción. Este método debe ser sobrescrito por subclases de Action."""
        raise NotImplementedError()


class PickupAction(Action):
    """Acción de recoger un objeto y añadirlo al inventario si hay espacio."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        # Itera sobre los objetos en el mapa buscando uno en la misma ubicación
        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                # Si el inventario está lleno, lanza una excepción
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Tu inventario está lleno.")

                # Elimina el objeto del mapa y lo agrega al inventario
                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                # Añade un mensaje en el registro de mensajes
                self.engine.message_log.add_message(f"Has recogido {item.name}.")
                return

        # Si no hay objeto para recoger, lanza una excepción
        raise exceptions.Impossible("No hay nada para recoger.")


class ItemAction(Action):
    """Acción que involucra el uso de un objeto en el juego, como un consumible o un equipo."""

    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item  # El objeto con el que se interactúa
        if not target_xy:
            target_xy = entity.x, entity.y  # Si no se proporciona una ubicación, se usa la ubicación de la entidad
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Devuelve el actor en la ubicación de destino de esta acción."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Ejecuta la habilidad del objeto. Este método invoca la acción adecuada para el objeto."""
        if self.item.consumable:
            self.item.consumable.activate(self)  # Si el objeto es consumible, se activa


class DropItem(ItemAction):
    """Acción de soltar un objeto del inventario."""

    def perform(self) -> None:
        # Si el objeto está equipado, se des equipa primero
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        # Luego se elimina del inventario
        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    """Acción de equipar un objeto, como una armadura o arma."""

    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)
        self.item = item  # El objeto que se va a equipar

    def perform(self) -> None:
        """Equipa o desequipa el objeto según su estado."""
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    """Acción de esperar sin realizar ninguna acción."""

    def perform(self) -> None:
        pass  # No hace nada, solo pasa


class TakeStairsAction(Action):
    """Acción de bajar por una escalera si está presente en la ubicación de la entidad."""

    def perform(self) -> None:
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            # Si la ubicación de la entidad es la de la escalera, genera un nuevo piso
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "Bajas la escalera.", color.descend
            )
        else:
            # Si no hay escalera, lanza una excepción
            raise exceptions.Impossible("No hay ninguna escalera aquí.")


class ActionWithDirection(Action):
    """Acción que tiene una dirección (movimiento o ataque)."""

    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)
        self.dx = dx  # Desplazamiento en X
        self.dy = dy  # Desplazamiento en Y

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Devuelve la ubicación de destino de esta acción (desplazamiento calculado)."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Devuelve la entidad que bloquea la ubicación de destino."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Devuelve el actor en la ubicación de destino."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    """Acción de ataque cuerpo a cuerpo."""

    def perform(self) -> None:
        target = self.target_actor  # Actor en la ubicación de destino
        if not target:
            raise exceptions.Impossible("Nada a lo que atacar.")  # Si no hay objetivo, lanza una excepción

        damage = self.entity.fighter.power - target.fighter.defense  # Calcula el daño

        attack_desc = f"{self.entity.name.capitalize()} ataca a {target.name}."
        # Define el color de la acción de ataque según si es el jugador o un enemigo
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            # Si el daño es positivo, inflige el daño al objetivo
            self.engine.message_log.add_message(
                f"{attack_desc} Hace {damage} puntos de daño.", attack_color
            )
            target.fighter.hp -= damage
        else:
            # Si el daño es 0 o negativo, el ataque no afecta
            self.engine.message_log.add_message(
                f"{attack_desc} pero no afecta a {target.name}.", attack_color
            )


class MovementAction(ActionWithDirection):
    """Acción de movimiento (caminar o desplazarse)."""

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy  # Ubicación de destino

        # Comprueba si el destino está fuera de los límites del mapa
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            raise exceptions.Impossible("Esto es una pared.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            raise exceptions.Impossible("Esto es una pared.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            raise exceptions.Impossible("Esto es una pared.")

        # Si no hay obstáculos, mueve la entidad
        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    """Acción de colisión, decide si se ataca o se mueve."""

    def perform(self) -> None:
        if self.target_actor:
            # Si hay un actor en la ubicación de destino, se realiza un ataque cuerpo a cuerpo
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            # Si no hay actor, se realiza un movimiento
            return MovementAction(self.entity, self.dx, self.dy).perform()