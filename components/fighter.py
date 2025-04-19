from __future__ import annotations

from typing import TYPE_CHECKING

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

# Importación condicional para la clase Actor solo en tiempo de comprobación de tipos
if TYPE_CHECKING:
    from entity import Actor  # Importa la clase Actor para el tipo de 'parent' de Fighter


class Fighter(BaseComponent):
    """Componente que representa las estadísticas de combate de un Actor (salud, defensa, poder de ataque)."""

    parent: Actor  # El Actor al que pertenece este componente Fighter

    def __init__(self, hp: int, base_defense: int, base_power: int):
        """Inicializa el Fighter con valores base para salud (hp), defensa y poder de ataque."""
        self.max_hp = hp  # Salud máxima
        self._hp = hp  # Salud actual
        self.base_defense = base_defense  # Defensa base
        self.base_power = base_power  # Poder base de ataque
        self.defensive_turns = 0  # Turnos restantes de inmunidad al daño.
        self.defense_bonus_turns = 0  # Turnos restantes del bono de defensa.
        self.temp_defense_bonus = 0  # Bono de defensa temporal.

    @property
    def hp(self) -> int:
        """Obtiene la salud actual."""
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        """Establece la salud, asegurando que no sea menor que 0 ni mayor que la salud máxima."""
        self._hp = max(0, min(value, self.max_hp))  # Limita la salud entre 0 y el valor máximo
        if self._hp == 0 and self.parent.ai:
            self.die()  # Si la salud llega a 0, el actor muere

    @property
    def defense(self) -> int:
        """Obtiene la defensa total del actor, incluyendo el bono temporal."""
        return self.base_defense + self.defense_bonus + self.temp_defense_bonus

    @property
    def power(self) -> int:
        """Obtiene el poder de ataque total del actor, sumando el poder base y el bono de poder de equipo."""
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        """Obtiene el bono de defensa proporcionado por el equipo del actor (si tiene)."""
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus  # Retorna el bono de defensa del equipo
        else:
            return 0  # Si no tiene equipo, no hay bono

    @property
    def power_bonus(self) -> int:
        """Obtiene el bono de poder de ataque proporcionado por el equipo del actor (si tiene)."""
        if self.parent.equipment:
            return self.parent.equipment.power_bonus  # Retorna el bono de poder del equipo
        else:
            return 0  # Si no tiene equipo, no hay bono

    def die(self) -> None:
        """Se ejecuta cuando el actor muere. Cambia su estado y muestra un mensaje de muerte."""
        # Si el actor es el jugador, se muestra un mensaje de muerte personalizado
        if self.engine.player is self.parent:
            self.engine.last_player_name = self.parent.name  # Guarda el nombre del jugador antes de cambiarlo
            death_message = "Has muerto"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} esta muerto"
            death_message_color = color.enemy_die

        # Cambia el carácter del actor para reflejar que está muerto
        self.parent.char = "%"
        self.parent.color = (191, 0, 0)  # Rojo para indicar que está muerto
        self.parent.blocks_movement = False  # Deja que los demás actores pasen por él
        self.parent.ai = None  # El actor deja de tener IA
        self.parent.render_order = RenderOrder.CORPSE  # Lo marca como cadáver para la renderización

        # Muestra el mensaje de muerte en el log
        self.engine.message_log.add_message(death_message, death_message_color)

        # El jugador gana experiencia por matar al actor (si el actor muerto tiene experiencia asignada)
        self.engine.player.level.add_xp(self.parent.level.xp_given)

    def heal(self, amount: int) -> int:
        """Recupera salud al actor, hasta el máximo de salud."""
        if self.hp == self.max_hp:
            return 0  # Si ya está al máximo, no se recupera nada

        new_hp_value = self.hp + amount  # Calcula la nueva salud

        # Asegura que la nueva salud no exceda el máximo
        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp  # Calcula la cantidad recuperada

        self.hp = new_hp_value  # Establece la nueva salud

        return amount_recovered  # Retorna la cantidad recuperada

    def take_damage(self, amount: int) -> None:
        """Reduce la salud del actor por la cantidad de daño recibido."""
        if self.defensive_turns > 0:
            self.engine.message_log.add_message(
                f"{self.parent.name} ignora el dano gracias al efecto defensivo.",
                color.status_effect_applied,
            )
            return  # Ignora el daño si está en modo defensivo.

        self.hp -= amount  # Reduce la salud según el daño recibido

    def activate_defensive_mode(self, turns: int) -> None:
        """Activa el modo defensivo, ignorando daño por un número de turnos."""
        self.defensive_turns = turns

    def activate_defense_bonus(self, bonus: int, turns: int) -> None:
        """Activa un bono de defensa temporal."""
        self.temp_defense_bonus += bonus
        self.defense_bonus_turns = turns

    def on_turn_end(self) -> None:
        """Se ejecuta al final de cada turno, reduciendo los turnos restantes de inmunidad al daño."""
        if self.defensive_turns > 0:
            self.defensive_turns -= 1
        if self.defense_bonus_turns > 0:
            self.defense_bonus_turns -= 1
        if self.defense_bonus_turns == 0 and self.temp_defense_bonus > 0:
            self.engine.message_log.add_message(
                f"{self.parent.name} siente que su piel vuelve a la normalidad.",
                color.status_effect_applied,
            )
            self.temp_defense_bonus = 0  # Elimina el bono de defensa temporal.