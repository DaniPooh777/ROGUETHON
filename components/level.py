from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

# Importación condicional para la clase Actor solo en tiempo de comprobación de tipos
if TYPE_CHECKING:
    from entity import Actor  # Importa la clase Actor para el tipo de 'parent' en la clase Level


class Level(BaseComponent):
    """Componente que gestiona el nivel, la experiencia y el aumento de nivel de un Actor."""
    
    parent: Actor  # Actor al que pertenece este componente de nivel

    def __init__(
        self,
        current_level: int = 1,  # Nivel actual
        current_xp: int = 0,  # Experiencia acumulada
        level_up_base: int = 0,  # Base de experiencia necesaria para subir de nivel
        level_up_factor: int = 150,  # Factor que incrementa la experiencia necesaria por cada nivel
        xp_given: int = 0,  # Experiencia otorgada por la acción realizada
    ):
        """Inicializa el componente de nivel con los valores predeterminados."""
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        """Calcula la experiencia necesaria para subir al siguiente nivel."""
        return self.level_up_base + self.current_level * self.level_up_factor

    @property
    def requires_level_up(self) -> bool:
        """Determina si el actor ha acumulado suficiente experiencia para subir de nivel."""
        return self.current_xp >= self.experience_to_next_level

    def add_xp(self, xp: int) -> None:
        """Añade experiencia al actor y verifica si debe subir de nivel."""
        if xp == 0 or self.level_up_base == 0:
            return  # Si la experiencia es 0 o no hay una base de nivel, no hace nada

        self.current_xp += xp  # Suma la experiencia

        # Mensaje de log para informar de la experiencia ganada
        self.engine.message_log.add_message(f"Has ganado {xp} puntos de experiencia.")

        # Si el actor ha alcanzado suficiente experiencia para subir de nivel
        if self.requires_level_up:
            # Informa sobre el nivel alcanzado
            self.engine.message_log.add_message(
                f"Has subido al nivel {self.current_level + 1}!"
            )

    def increase_level(self) -> None:
        """Aumenta el nivel del actor, deduciendo la experiencia necesaria."""
        self.current_xp -= self.experience_to_next_level  # Resta la experiencia usada para subir de nivel

        self.current_level += 1  # Incrementa el nivel

    def increase_max_hp(self, amount: int = 20) -> None:
        """Aumenta la salud máxima del actor (y la salud actual) cuando sube de nivel."""
        self.parent.fighter.max_hp += amount  # Aumenta la salud máxima
        self.parent.fighter.hp += amount  # Restaura la salud al máximo

        # Mensaje de log indicando que el actor se siente más vigoroso
        self.engine.message_log.add_message("Te sientes con mas vigor.")

        self.increase_level()  # Aumenta el nivel del actor después de mejorar su salud

    def increase_power(self, amount: int = 1) -> None:
        """Aumenta el poder de ataque base del actor cuando sube de nivel."""
        self.parent.fighter.base_power += amount  # Aumenta el poder de ataque

        # Mensaje de log indicando que el actor se siente más fuerte
        self.engine.message_log.add_message("Te sientes mas fuerte.")

        self.increase_level()  # Aumenta el nivel del actor después de mejorar su poder

    def increase_defense(self, amount: int = 1) -> None:
        """Aumenta la defensa base del actor cuando sube de nivel."""
        self.parent.fighter.base_defense += amount  # Aumenta la defensa base

        # Mensaje de log indicando que el actor se siente más robusto
        self.engine.message_log.add_message("Te sientes mas robusto.")

        self.increase_level()  # Aumenta el nivel del actor después de mejorar su defensa