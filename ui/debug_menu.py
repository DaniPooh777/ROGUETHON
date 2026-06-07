"""
Modo Debugger — Menú de desarrollo para probar features rápidamente.
Acceso: presionar F1 durante el juego.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import tcod.event

from ui.input_handlers import AskUserEventHandler, MainGameEventHandler

if TYPE_CHECKING:
    from core.engine import Engine


def _get_number_key(event: tcod.event.KeyDown) -> Optional[int]:
    """Devuelve el número presionado (1-9) o None si no es un número."""
    # Números del teclado principal (ASCII 49-57 = '1'-'9')
    if 49 <= event.sym <= 57:
        return event.sym - 48  # Convertir ASCII a número
    return None


class DebugMenuHandler(AskUserEventHandler):
    """Menú principal de debug — acceso con F1."""

    TITLE = "      MODO DEBUG      "

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.KeySym.F1:
            return MainGameEventHandler(self.engine)  # Cerrar con F1

        num = _get_number_key(event)
        if num == 1:
            return DebugGoToFloorHandler(self.engine)
        if num == 2:
            return DebugEditStatsHandler(self.engine)
        if num == 3:
            return self._toggle_god_mode()
        if num == 4:
            return DebugAddItemHandler(self.engine)
        if num == 5:
            return DebugSpawnEnemyHandler(self.engine)

        return None  # Ignorar otras teclas

    def _toggle_god_mode(self) -> Optional[MainGameEventHandler]:
        engine = self.engine
        player = engine.player
        fighter = player.fighter

        if engine.debug_god_mode:
            # Desactivar — restaurar stats originales
            if engine.debug_original_stats:
                fighter.max_hp = engine.debug_original_stats["max_hp"]
                fighter.hp = engine.debug_original_stats["hp"]
                fighter.base_defense = engine.debug_original_stats["base_defense"]
                fighter.base_power = engine.debug_original_stats["base_power"]
            engine.debug_god_mode = False
            engine.message_log.add_message("[DEBUG] God mode DESACTIVADO")
        else:
            # Activar — guardar stats y poner infinitos
            engine.debug_original_stats = {
                "max_hp": fighter.max_hp,
                "hp": fighter.hp,
                "base_defense": fighter.base_defense,
                "base_power": fighter.base_power,
            }
            fighter.max_hp = 9999
            fighter.hp = 9999
            fighter.base_defense = 99
            fighter.base_power = 99
            engine.debug_god_mode = True
            engine.message_log.add_message("[DEBUG] God mode ACTIVADO")

        return MainGameEventHandler(engine)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x, y = 40, 5
        width = len(self.TITLE) + 6

        console.draw_frame(
            x=x, y=y, width=width, height=12,
            title=self.TITLE,
            clear=True, fg=(255, 255, 0), bg=(0, 0, 0),
        )

        god_status = "ON" if self.engine.debug_god_mode else "OFF"
        console.print(x=x + 1, y=y + 1, string=f"[1] Ir a piso X")
        console.print(x=x + 1, y=y + 2, string=f"[2] Modificar stats")
        console.print(x=x + 1, y=y + 3, string=f"[3] God mode: {god_status}")
        console.print(x=x + 1, y=y + 4, string=f"[4] Agregar item")
        console.print(x=x + 1, y=y + 5, string=f"[5] Spawn enemigo")
        console.print(x=x + 1, y=y + 7, string=f"[F1] Cerrar menu")


# ==================== IR A PISO X ====================

class DebugGoToFloorHandler(AskUserEventHandler):
    """Permite saltar a cualquier piso."""

    TITLE = "      IR A PISO      "

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.KeySym.F1:
            return DebugMenuHandler(self.engine)

        floor = _get_number_key(event)
        if floor is not None:
            engine = self.engine
            # Generar piso deseado
            engine.game_world.current_floor = floor - 1  # generate_floor incrementa
            engine.game_world.generate_floor()
            engine.update_fov()
            engine.message_log.add_message(f"[DEBUG] Saltaste al piso {floor}")
            return MainGameEventHandler(engine)

        return None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x, y = 40, 8
        width = len(self.TITLE) + 6

        console.draw_frame(
            x=x, y=y, width=width, height=7,
            title=self.TITLE,
            clear=True, fg=(255, 255, 0), bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string="Presiona 1-9 para ir al piso")
        console.print(x=x + 1, y=y + 3, string=f"Piso actual: {self.engine.game_world.current_floor}")
        console.print(x=x + 1, y=y + 5, string="[F1] Cancelar")


# ==================== MODIFICAR STATS ====================

class DebugEditStatsHandler(AskUserEventHandler):
    """Permite modificar stats del jugador."""

    TITLE = "      MODIFICAR STATS      "

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.KeySym.F1:
            return DebugMenuHandler(self.engine)

        fighter = self.engine.player.fighter

        if event.sym == tcod.event.KeySym.H:
            fighter.hp = fighter.max_hp
            self.engine.message_log.add_message("[DEBUG] HP restaurado al maximo")
            return DebugEditStatsHandler(self.engine)
        if event.sym == tcod.event.KeySym.M:
            fighter.max_hp += 10
            fighter.hp = fighter.max_hp
            self.engine.message_log.add_message("[DEBUG] Max HP +10")
            return DebugEditStatsHandler(self.engine)
        if event.sym == tcod.event.KeySym.P:
            fighter.base_power += 2
            self.engine.message_log.add_message("[DEBUG] Poder +2")
            return DebugEditStatsHandler(self.engine)
        if event.sym == tcod.event.KeySym.D:
            fighter.base_defense += 2
            self.engine.message_log.add_message("[DEBUG] Defensa +2")
            return DebugEditStatsHandler(self.engine)

        return None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x, y = 35, 6
        width = len(self.TITLE) + 6

        console.draw_frame(
            x=x, y=y, width=width, height=11,
            title=self.TITLE,
            clear=True, fg=(255, 255, 0), bg=(0, 0, 0),
        )

        f = self.engine.player.fighter
        console.print(x=x + 1, y=y + 1, string=f"HP: {f.hp}/{f.max_hp}")
        console.print(x=x + 1, y=y + 2, string=f"Poder: {f.base_power}")
        console.print(x=x + 1, y=y + 3, string=f"Defensa: {f.base_defense}")
        console.print(x=x + 1, y=y + 5, string="[H] Curar todo")
        console.print(x=x + 1, y=y + 6, string="[M] Max HP +10")
        console.print(x=x + 1, y=y + 7, string="[P] Poder +2")
        console.print(x=x + 1, y=y + 8, string="[D] Defensa +2")
        console.print(x=x + 1, y=y + 9, string="[F1] Volver")


# ==================== AGREGAR ITEM ====================

class DebugAddItemHandler(AskUserEventHandler):
    """Permite agregar items al inventario."""

    TITLE = "      AGREGAR ITEM      "

    def __init__(self, engine: Engine):
        super().__init__(engine)
        import entities.factories as factories
        self.items = [
            ("Pocion de salud", factories.health_potion),
            ("Pocion de salud mayor", factories.greater_health_potion),
            ("Pergamino de confusion", factories.confusion_scroll),
            ("Pergamino de fuego", factories.fireball_scroll),
            ("Pergamino relampago", factories.lightning_scroll),
            ("Pergamino defensivo", factories.defensive_scroll),
            ("Pergamino invisible", factories.invisibility_scroll),
            ("Pergamino de inmunidad", factories.immunity_scroll),
            ("Daga", factories.dagger),
            ("Espada", factories.sword),
            ("Armadura de cuero", factories.leather_armor),
            ("Armadura de hierro", factories.chain_mail),
        ]

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.KeySym.F1:
            return DebugMenuHandler(self.engine)

        num = _get_number_key(event)
        if num is not None and 1 <= num <= len(self.items):
            idx = num - 1
            name, item_factory = self.items[idx]
            import copy
            item = copy.deepcopy(item_factory)
            self.engine.player.inventory.items.append(item)
            self.engine.message_log.add_message(f"[DEBUG] Agregado: {name}")
            return DebugAddItemHandler(self.engine)

        return None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x, y = 35, 3
        width = len(self.TITLE) + 6

        console.draw_frame(
            x=x, y=y, width=width, height=min(len(self.items) + 4, 18),
            title=self.TITLE,
            clear=True, fg=(255, 255, 0), bg=(0, 0, 0),
        )

        for i, (name, _) in enumerate(self.items[:9]):
            console.print(x=x + 1, y=y + 1 + i, string=f"[{i + 1}] {name}")

        console.print(x=x + 1, y=y + len(self.items) + 2, string="[F1] Volver")


# ==================== SPAWN ENEMIGO ====================

class DebugSpawnEnemyHandler(AskUserEventHandler):
    """Permite spawnear enemigos en la posición del jugador."""

    TITLE = "      SPAWN ENEMIGO      "

    def __init__(self, engine: Engine):
        super().__init__(engine)
        import entities.factories as factories
        self.enemies = [
            ("Rata", factories.rata),
            ("Orco", factories.orc),
            ("Goblin", factories.goblin),
            ("Troll", factories.troll),
            ("Esqueleto", factories.esqueleto),
            ("Mimic", factories.mimic),
            ("Dragon", factories.dragon),
        ]

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.KeySym.F1:
            return DebugMenuHandler(self.engine)

        num = _get_number_key(event)
        if num is not None and 1 <= num <= len(self.enemies):
            idx = num - 1
            name, enemy_factory = self.enemies[idx]
            enemy_factory.spawn(
                self.engine.game_map,
                self.engine.player.x,
                self.engine.player.y,
            )
            self.engine.message_log.add_message(f"[DEBUG] Spawn: {name}")
            return MainGameEventHandler(self.engine)

        return None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x, y = 35, 5
        width = len(self.TITLE) + 6

        console.draw_frame(
            x=x, y=y, width=width, height=len(self.enemies) + 4,
            title=self.TITLE,
            clear=True, fg=(255, 255, 0), bg=(0, 0, 0),
        )

        for i, (name, _) in enumerate(self.enemies):
            console.print(x=x + 1, y=y + 1 + i, string=f"[{i + 1}] {name}")

        console.print(x=x + 1, y=y + len(self.enemies) + 2, string="[F1] Volver")
