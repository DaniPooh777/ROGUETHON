from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

# Importación condicional para la clase Item solo en tiempo de comprobación de tipos
if TYPE_CHECKING:
    from entity import Item  # Importa la clase Item para el tipo de 'parent' de Equippable


class Equippable(BaseComponent):
    """Componente que representa un objeto que puede ser equipado, como armas o armaduras."""

    parent: Item  # El Item al que pertenece este componente Equippable

    def __init__(
        self,
        equipment_type: EquipmentType,  # Tipo de equipo (arma, armadura, etc.)
        power_bonus: int = 0,  # Bono de poder (para armas)
        defense_bonus: int = 0,  # Bono de defensa (para armaduras)
    ):
        """Inicializa un objeto equipable con su tipo y los bonos de poder y defensa."""
        self.equipment_type = equipment_type  # Establece el tipo de equipo (arma, armadura, etc.)

        self.power_bonus = power_bonus  # Establece el bono de poder para armas
        self.defense_bonus = defense_bonus  # Establece el bono de defensa para armaduras


class Dagger(Equippable):
    """Clase que representa una daga (objeto equipable de tipo 'arma')."""

    def __init__(self) -> None:
        """Inicializa una daga con un bono de poder de 2."""
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


class Sword(Equippable):
    """Clase que representa una espada (objeto equipable de tipo 'arma')."""

    def __init__(self) -> None:
        """Inicializa una espada con un bono de poder de 4."""
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


class LeatherArmor(Equippable):
    """Clase que representa una armadura de cuero (objeto equipable de tipo 'armadura')."""

    def __init__(self) -> None:
        """Inicializa una armadura de cuero con un bono de defensa de 1."""
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)


class ChainMail(Equippable):
    """Clase que representa una cota de malla (objeto equipable de tipo 'armadura')."""

    def __init__(self) -> None:
        """Inicializa una cota de malla con un bono de defensa de 3."""
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)