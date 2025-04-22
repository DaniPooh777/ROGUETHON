"""
Este código define un sistema para gestionar objetos equipables (armas y armaduras) en un juego.
Los objetos equipables tienen atributos como bonificaciones de poder (para armas) y defensa (para armaduras),
y el sistema está diseñado para facilitar la adición de nuevos tipos de equipo. 
Así, cada objeto influye en las habilidades o estadísticas de los personajes que los equipan.
"""

from __future__ import annotations # Se asegura de que las anotaciones de tipo que contienen referencias a clases se resuelvan correctamente.
from typing import TYPE_CHECKING # Importamos TYPE_CHECKING para realizar comprobaciones de tipos solo durante la fase de desarrollo.
from components.base_component import BaseComponent # Importamos la clase base 'BaseComponent' que sirve como clase base para todos los componentes en el sistema.
from equipment_types import EquipmentType # Importamos el enum 'EquipmentType' que define los diferentes tipos de equipo que puede existir (arma, armadura, etc.)

# Importación condicional para la clase 'Item', que solo ocurre en la fase de comprobación de tipos, mejorando la eficiencia en tiempo de ejecución.
if TYPE_CHECKING:
    from entity import Item  # Importa la clase Item para usarla como tipo en el componente Equippable

# Clase principal que representa a los objetos equipables. Esta clase hereda de BaseComponent.
class Equippable(BaseComponent):
    """Componente que representa un objeto que puede ser equipado, como armas o armaduras."""

    # Definimos el atributo 'parent', que hace referencia al objeto 'Item' al que pertenece este componente equipable.
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,  # Tipo de equipo, que puede ser un arma, una armadura, etc.
        power_bonus: int = 0,  # Bono de poder, utilizado solo para armas (por defecto es 0)
        defense_bonus: int = 0,  # Bono de defensa, utilizado solo para armaduras (por defecto es 0)
    ):
        """Inicializa un objeto equipable con su tipo y los bonos de poder y defensa."""
        
        # Asignamos el tipo de equipo (arma, armadura, etc.)
        self.equipment_type = equipment_type
        
        # Asignamos el bono de poder para armas, que por defecto es 0.
        self.power_bonus = power_bonus
        
        # Asignamos el bono de defensa para armaduras, que por defecto es 0.
        self.defense_bonus = defense_bonus

class Dagger(Equippable):
    """Clase que representa una daga (objeto equipable de tipo 'arma')."""

    def __init__(self) -> None:
        """Inicializa una daga con un bono de poder de 2."""
        # Llamamos al constructor de la clase base 'Equippable' con el tipo de equipo WEAPON y un bono de poder de 2.
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


class Sword(Equippable):
    """Clase que representa una espada (objeto equipable de tipo 'arma')."""

    def __init__(self) -> None:
        """Inicializa una espada con un bono de poder de 4."""
        # Llamamos al constructor de la clase base 'Equippable' con el tipo de equipo WEAPON y un bono de poder de 4.
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


class LeatherArmor(Equippable):
    """Clase que representa una armadura de cuero (objeto equipable de tipo 'armadura')."""

    def __init__(self) -> None:
        """Inicializa una armadura de cuero con un bono de defensa de 1."""
        # Llamamos al constructor de la clase base 'Equippable' con el tipo de equipo ARMOR y un bono de defensa de 1.
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)


class ChainMail(Equippable):
    """Clase que representa una cota de malla (objeto equipable de tipo 'armadura')."""

    def __init__(self) -> None:
        """Inicializa una cota de malla con un bono de defensa de 3."""
        # Llamamos al constructor de la clase base 'Equippable' con el tipo de equipo ARMOR y un bono de defensa de 3.
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)