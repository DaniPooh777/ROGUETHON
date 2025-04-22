""" 
Este código define la clase 'Equipment', que es un componente que gestiona el equipo
de un actor dentro de un juego. Permite al actor equiparse con armas y armaduras,
calculando las bonificaciones de defensa y poder de los ítems equipados. Además,
proporciona funciones para equipar y desquitar ítems, y generar mensajes relacionados
con estos cambios (por ejemplo, cuando un ítem es equipado o desequipado).
"""
from __future__ import annotations  # Se asegura de que las anotaciones de tipo que contienen referencias a clases se resuelvan correctamente.
from typing import Optional, TYPE_CHECKING  # Importa las herramientas necesarias para anotaciones de tipo condicional y opcional.
from components.base_component import BaseComponent  # Importa la clase base para los componentes de entidad.
from equipment_types import EquipmentType  # Importa el tipo de equipo para diferenciar armas y armaduras.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from entity import Actor, Item  # Importa las clases Actor e Item solo durante la comprobación de tipos.

class Equipment(BaseComponent):
    """Componente que gestiona el equipo (armas y armaduras) de un actor."""
    parent: Actor  # Se refiere al actor que tiene este componente de equipo.

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None):
        """
        Inicializa el equipo con un arma y/o una armadura opcionales.

        :param weapon: El ítem de tipo arma que se equipa (opcional).
        :param armor: El ítem de tipo armadura que se equipa (opcional).
        """
        self.weapon = weapon  # Arma equipada, si hay alguna.
        self.armor = armor  # Armadura equipada, si hay alguna.

    @property
    def defense_bonus(self) -> int:
        """
        Devuelve la bonificación total de defensa del equipo (suma de las bonificaciones de armamento y armadura).

        Esta propiedad calcula el bono de defensa considerando tanto el arma equipada como la armadura equipada,
        si es que existen.

        :return: La bonificación total de defensa.
        """
        bonus = 0  # Inicializa la bonificación total de defensa.

        # Si el arma equipada tiene una bonificación de defensa, se añade al bonus total.
        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        # Si la armadura equipada tiene una bonificación de defensa, se añade al bonus total.
        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus  # Devuelve el bono de defensa total.

    @property
    def power_bonus(self) -> int:
        """
        Devuelve la bonificación total de poder del equipo (suma de las bonificaciones de armamento y armadura).

        Similar a la bonificación de defensa, pero calcula el bono de poder considerando las bonificaciones
        de las armas y armaduras equipadas.

        :return: La bonificación total de poder.
        """
        bonus = 0  # Inicializa la bonificación total de poder.

        # Si el arma equipada tiene una bonificación de poder, se añade al bonus total.
        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        # Si la armadura equipada tiene una bonificación de poder, se añade al bonus total.
        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus  # Devuelve el bono de poder total.

    def item_is_equipped(self, item: Item) -> bool:
        """
        Devuelve True si el item dado está equipado (en el arma o armadura).

        Verifica si el ítem proporcionado es el que está actualmente equipado en el actor (ya sea como arma o armadura).

        :param item: El ítem a verificar.
        :return: Verdadero si el ítem está equipado, de lo contrario Falso.
        """
        return self.weapon == item or self.armor == item  # Verifica si el ítem está en el arma o la armadura equipada.

    def unequip_message(self, item_name: str) -> None:
        """
        Añade un mensaje al registro de mensajes al desquitar un ítem.

        Esta función se invoca para mostrar un mensaje cuando un ítem es desquitado del actor.

        :param item_name: El nombre del ítem desquitado.
        """
        self.parent.gamemap.engine.message_log.add_message(
            f"Te has quitado {item_name}."  # Añade el mensaje correspondiente al registro.
        )

    def equip_message(self, item_name: str) -> None:
        """
        Añade un mensaje al registro de mensajes al equipar un ítem.

        Esta función se invoca para mostrar un mensaje cuando un ítem es equipado al actor.

        :param item_name: El nombre del ítem equipado.
        """
        self.parent.gamemap.engine.message_log.add_message(
            f"Te has equipado {item_name}."  # Añade el mensaje correspondiente al registro.
        )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        """
        Equipa un ítem al slot especificado (arma o armadura).

        Este método coloca un ítem en un slot específico (ya sea para un arma o armadura) y maneja la
        lógica de desquitar el ítem actual si es necesario.

        :param slot: El nombre del slot en el que se va a equipar el ítem (arma o armadura).
        :param item: El ítem a equipar.
        :param add_message: Indica si debe agregarse un mensaje al registro (si es True, se agrega el mensaje).
        """
        current_item = getattr(self, slot)  # Obtiene el ítem actual en el slot especificado.

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)  # Si hay un ítem actual, se desquita antes de equipar el nuevo.

        setattr(self, slot, item)  # Asigna el nuevo ítem al slot especificado.

        if add_message:
            self.equip_message(item.name)  # Muestra un mensaje indicando que el ítem fue equipado.

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        """
        Desquita el ítem de un slot (arma o armadura).

        El método permite desquitar un ítem de un slot (arma o armadura) y maneja la lógica de agregar
        mensajes al registro si se requiere.

        :param slot: El nombre del slot del que se va a desquitar el ítem (arma o armadura).
        :param add_message: Indica si se debe agregar un mensaje al registro (si es True, se agrega el mensaje).
        """
        current_item = getattr(self, slot)  # Obtiene el ítem actual en el slot especificado.

        if add_message and current_item is not None:
            self.unequip_message(current_item.name)  # Muestra un mensaje si hay un ítem que desquitar.

        setattr(self, slot, None)  # Desquita el ítem del slot especificado.

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        """
        Activa o desactiva el equipo de un ítem, dependiendo de si está equipado o no.

        Este método alterna entre equipar y desquitar un ítem. Si el ítem está equipado, se desquita,
        de lo contrario, se equipa. El tipo de equipo se determina automáticamente en función del tipo
        de equipo del ítem (arma o armadura).

        :param equippable_item: El ítem que se va a equipar o desquitar.
        :param add_message: Indica si se debe agregar un mensaje al registro (si es True, se agrega el mensaje).
        """
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"  # Si el ítem es un arma, se asigna al slot de "weapon".
        else:
            slot = "armor"  # Si el ítem es una armadura, se asigna al slot de "armor".

        # Si el ítem ya está equipado en ese slot, lo desquita; de lo contrario, lo equipa.
        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)