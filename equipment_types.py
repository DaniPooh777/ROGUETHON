# Importación de módulos para trabajar con enumeraciones.
from enum import auto, Enum

# Definición de un tipo de enumeración llamado EquipmentType, que representa los tipos de equipo que un personaje puede usar.
class EquipmentType(Enum):
    # Asigna automáticamente un valor único para cada tipo de equipo
    WEAPON = auto()  # Representa un arma, el valor será asignado automáticamente (1, por ejemplo)
    ARMOR = auto()    # Representa una armadura, el valor también será asignado automáticamente (2, por ejemplo)
