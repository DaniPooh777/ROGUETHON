"""
Este módulo define el sistema de hambre del jugador.
El hambre disminuye con cada acción y afecta la precisión y poder de ataque.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entities.entity import Actor


class Hunger(BaseComponent):
    """
    Componente que gestiona el estado de hambre del jugador.
    El hambre disminuye cada turno y afecta las capacidades de combate.
    """
    
    parent: Actor
    
    def __init__(self, max_hunger: int = 1000):
        """
        Inicializa el sistema de hambre.
        
        Args:
            max_hunger: Hambre máxima (default 1000)
        """
        self.max_hunger = max_hunger
        self.current_hunger = max_hunger
    
    @property
    def state(self) -> str:
        """
        Retorna el estado actual del hambre.
        
        Returns:
            "satisfied": 800-1000 (sin efectos)
            "hungry": 500-799 (-10% precisión)
            "weak": 200-499 (-25% precisión, -25% poder)
            "moribund": 0-199 (no puede actuar)
        """
        if self.current_hunger >= 800:
            return "satisfied"
        elif self.current_hunger >= 500:
            return "hungry"
        elif self.current_hunger >= 200:
            return "weak"
        else:
            return "moribund"
    
    @property
    def hit_chance(self) -> int:
        """
        Retorna el porcentaje de golpe según el estado de hambre.
        
        Returns:
            100: satisfied (nunca falla)
            90: hungry (10% fallar)
            75: weak (25% fallar)
            50: moribund (50% fallar)
        """
        if self.state == "satisfied":
            return 100
        elif self.state == "hungry":
            return 90
        elif self.state == "weak":
            return 75
        else:  # moribund
            return 50  # 50% de chance de fallar
    
    @property
    def is_moribund(self) -> bool:
        """Verifica si el jugador está moribundo."""
        return self.current_hunger < 200
    
    def eat(self, amount: int) -> None:
        """
        Restaura hambre al jugador.
        
        Args:
            amount: Cantidad de hambre a restaurar
        """
        self.current_hunger = min(self.max_hunger, self.current_hunger + amount)
    
    def on_turn_end(self) -> None:
        """Se ejecuta al final de cada turno, reduciendo la hambre."""
        if self.current_hunger > 0:
            self.current_hunger -= 1
        
        # Verificar muerte por hambre si llega a 0
        if self.current_hunger <= 0:
            self.parent.fighter.die()  # El fighter matará al jugador