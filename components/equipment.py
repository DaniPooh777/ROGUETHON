from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

# Importación condicional de clases para comprobación de tipos.
if TYPE_CHECKING:
    from entity import Actor, Item  # Importa las clases Actor e Item solo durante la comprobación de tipos


class Equipment(BaseComponent):
    """Componente que gestiona el equipo (armas y armaduras) de un actor."""

    parent: Actor  # Actor al que pertenece este componente de equipo

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None):
        """Inicializa el equipo con un arma y/o una armadura opcionales."""
        self.weapon = weapon  # Arma equipada (si la hay)
        self.armor = armor  # Armadura equipada (si la hay)

    @property
    def defense_bonus(self) -> int:
        """Devuelve la bonificación total de defensa del equipo (suma de las bonificaciones de armamento y armadura)."""
        bonus = 0

        # Si el arma equipada tiene una bonificación de defensa, se añade al bonus total.
        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        # Si la armadura equipada tiene una bonificación de defensa, se añade al bonus total.
        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        """Devuelve la bonificación total de poder del equipo (suma de las bonificaciones de armamento y armadura)."""
        bonus = 0

        # Si el arma equipada tiene una bonificación de poder, se añade al bonus total.
        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        # Si la armadura equipada tiene una bonificación de poder, se añade al bonus total.
        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        """Devuelve True si el item dado está equipado (en el arma o armadura)."""
        return self.weapon == item or self.armor == item

    def unequip_message(self, item_name: str) -> None:
        """Añade un mensaje al registro de mensajes al desquitar un ítem."""
        self.parent.gamemap.engine.message_log.add_message(
            f"Te has quitado {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        """Añade un mensaje al registro de mensajes al equipar un ítem."""
        self.parent.gamemap.engine.message_log.add_message(
            f"Te has equipado {item_name}."
        )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        """Equipa un ítem al slot especificado (arma o armadura)."""
        current_item = getattr(self, slot)  # Obtiene el ítem actual en el slot

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)  # Desquita el ítem actual si hay uno

        setattr(self, slot, item)  # Equipa el nuevo ítem en el slot especificado

        if add_message:
            self.equip_message(item.name)  # Muestra un mensaje indicando que el ítem fue equipado

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        """Desquita el ítem de un slot (arma o armadura)."""
        current_item = getattr(self, slot)  # Obtiene el ítem actual en el slot

        if add_message and current_item is not None:
            self.unequip_message(current_item.name)  # Muestra un mensaje indicando que el ítem fue desquitado

        setattr(self, slot, None)  # Desquita el ítem del slot

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        """Activa o desactiva el equipo de un ítem, dependiendo de si está equipado o no."""
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"  # Si el ítem es un arma, se asigna al slot de "weapon"
        else:
            slot = "armor"  # Si el ítem es una armadura, se asigna al slot de "armor"

        # Si el ítem ya está equipado en ese slot, lo desquita; de lo contrario, lo equipa.
        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)