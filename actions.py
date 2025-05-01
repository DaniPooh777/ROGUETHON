"""
Este módulo define las diferentes acciones que los actores pueden realizar en el juego, como moverse, atacar, recoger objetos, etc.
Cada acción está representada por una clase que hereda de la clase base Action.
"""

from __future__ import annotations  # Permite usar anotaciones de tipo en clases antes de su definición completa.
from typing import Optional, Tuple, TYPE_CHECKING  # Importa herramientas para la comprobación de tipos y anotaciones.

import color  # Módulo para manejar colores en los mensajes
import exceptions  # Excepciones personalizadas para manejar errores en el juego
import tile_types  # Tipos de tiles usados en el mapa del juego

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from engine import Engine  # La clase Engine, que maneja la lógica del juego
    from entity import Actor, Entity, Item  # Clases Actor, Entity y Item para las entidades del juego


class Action:
    """Acción base que se realiza en el juego. Las acciones específicas como mover o atacar heredan de esta clase."""

    def __init__(self, entity: Actor) -> None:
        super().__init__()  # Llama al constructor de la clase base
        self.entity = entity  # La entidad que realiza la acción (por ejemplo, el jugador o un enemigo)

    @property # Define un método como una propiedad, permitiendo acceder a él como si fuera un atributo.
    def engine(self) -> Engine:
        """Devuelve el motor (Engine) al que pertenece esta acción."""
        return self.entity.gamemap.engine  # Obtiene el motor desde el mapa de la entidad

    def perform(self) -> None:
        """Realiza la acción. Este método debe ser sobrescrito por subclases de Action."""
        raise NotImplementedError()  # Lanza un error si no se implementa en una subclase


class PickupAction(Action):
    """Acción de recoger un objeto y añadirlo al inventario si hay espacio."""

    def __init__(self, entity: Actor):
        super().__init__(entity)  # Llama al constructor de la clase base

    def perform(self) -> None:
        actor_location_x = self.entity.x  # Obtiene la posición X del actor
        actor_location_y = self.entity.y  # Obtiene la posición Y del actor
        inventory = self.entity.inventory  # Obtiene el inventario del actor

        # Itera sobre los objetos en el mapa buscando uno en la misma ubicación
        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                # Si el inventario está lleno, lanza una excepción
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Tu inventario está lleno.")

                # Elimina el objeto del mapa y lo agrega al inventario
                self.engine.game_map.entities.remove(item)  # Elimina el objeto del mapa
                item.parent = self.entity.inventory  # Asigna el inventario como padre del objeto
                inventory.items.append(item)  # Añade el objeto al inventario

                # Añade un mensaje en el registro de mensajes
                self.engine.message_log.add_message(f"Has recogido {item.name}.")
                return  # Termina la acción después de recoger el objeto

        # Si no hay objeto para recoger, lanza una excepción
        raise exceptions.Impossible("No hay nada para recoger.")


class ItemAction(Action):
    """Acción que involucra el uso de un objeto en el juego, como un consumible o un equipo."""

    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)  # Llama al constructor de la clase base
        self.item = item  # El objeto con el que se interactúa
        if not target_xy:
            target_xy = entity.x, entity.y  # Si no se proporciona una ubicación, se usa la ubicación de la entidad
        self.target_xy = target_xy  # Asigna la ubicación objetivo

    @property
    def target_actor(self) -> Optional[Actor]:
        """Devuelve el actor en la ubicación de destino de esta acción."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)  # Obtiene el actor en la ubicación objetivo

    def perform(self) -> None:
        """Ejecuta la habilidad del objeto. Este método invoca la acción adecuada para el objeto."""
        if self.item.consumable:
            try:
                self.item.consumable.activate(self)  # Si el objeto es consumible, se activa
            except exceptions.Impossible as exc:
                self.engine.message_log.add_message(str(exc), color.impossible)  # Maneja la excepción Impossible
                return


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
        super().__init__(entity)  # Llama al constructor de la clase base
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
            raise exceptions.Impossible("No hay ninguna escalera aqui.")


class ActionWithDirection(Action):
    """Acción que tiene una dirección (movimiento o ataque)."""

    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)  # Llama al constructor de la clase base
        self.dx = dx  # Desplazamiento en X
        self.dy = dy  # Desplazamiento en Y

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Devuelve la ubicación de destino de esta acción (desplazamiento calculado)."""
        return self.entity.x + self.dx, self.entity.y + self.dy  # Calcula la ubicación de destino

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Devuelve la entidad que bloquea la ubicación de destino."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)  # Obtiene la entidad bloqueante

    @property
    def target_actor(self) -> Optional[Actor]:
        """Devuelve el actor en la ubicación de destino."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)  # Obtiene el actor en la ubicación de destino

    def perform(self) -> None:
        raise NotImplementedError()  # Lanza un error si no se implementa en una subclase


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
                f"{attack_desc} Hace {damage} puntos de dano.", attack_color
            )
            target.fighter.hp -= damage
        else:
            # Si el daño es 0 o negativo, el ataque solo hace 1 de daño
            self.engine.message_log.add_message(
                f"{attack_desc} Hace 1 punto de dano.", attack_color
            )
            target.fighter.hp -= 1


class MovementAction(ActionWithDirection):
    """Acción de movimiento (caminar o desplazarse)."""

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy  # Obtiene la ubicación de destino

        # Comprueba si el destino está fuera de los límites del mapa
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            self.engine.message_log.add_message("Esto es una pared.", color.impossible)
            return  # No hace nada si está fuera de los límites
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            self.engine.message_log.add_message("Esto es una pared.", color.impossible)
            return  # No hace nada si no es caminable
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # No hace nada si hay una entidad bloqueando

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


class RevealHiddenWallAction(Action):
    """Acción para revelar una pared falsa cuando el jugador interactúa con ella."""

    def __init__(self, entity: Actor, target_x: int, target_y: int):
        super().__init__(entity)  # Llama al constructor de la clase base
        self.target_x = target_x  # Coordenada X del objetivo
        self.target_y = target_y  # Coordenada Y del objetivo

    def perform(self) -> None:
        tile = self.engine.game_map.tiles[self.target_x, self.target_y]  # Obtiene el tile en la ubicación objetivo

        # Verifica si el tile es una pared falsa.
        if tile == tile_types.hidden_wall_tile:
            self.engine.game_map.tiles[self.target_x, self.target_y] = tile_types.floor  # Revela la pared.
            self.engine.message_log.add_message("Has descubierto una pared falsa.", color.player_atk)
        else:
            raise exceptions.Impossible("No hay nada que revelar aquí.")