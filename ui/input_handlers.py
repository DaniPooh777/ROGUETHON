"""
Este módulo gestiona los manejadores de eventos del juego, incluyendo la interacción del jugador, el inventario, y los eventos de combate.
Proporciona clases para manejar entradas del teclado, clics del ratón y renderizado de mensajes emergentes.
"""

from __future__ import (
    annotations,
)  # Permite el uso de anotaciones de tipo que se refieren a clases que aún no se han definido.
from systems.actions import (
    Action,
    BumpAction,
    PickupAction,
    RevealHiddenWallAction,
    WaitAction,
)  # Importa clases específicas del módulo de acciones.
from typing import (
    Callable,
    Optional,
    Tuple,
    TYPE_CHECKING,
    Union,
)  # Importa tipos para anotaciones.

import tcod  # Librería para desarrollo de juegos roguelike.
import libtcodpy  # Versión alternativa de la librería libtcod.
import systems.actions as actions  # Importa el módulo de acciones del juego.
from ui import colors as color  # Módulo para manejar colores en el juego.
import core.exceptions as exceptions  # Módulo que define excepciones personalizadas.
import core.tile_types as tile_types  # Módulo que define tipos de tiles (casillas) del mapa.
import os  # Módulo para interactuar con el sistema operativo.

# Este bloque solo importa las clases cuando se está realizando una comprobación de tipos, no se ejecuta en tiempo de ejecución.
if TYPE_CHECKING:
    from core.engine import Engine
    from entities.entity import Item


# Diccionario que asocia las teclas de dirección a los movimientos en el mapa.
# Cada tecla de dirección corresponde a un desplazamiento en el eje X o Y.
MOVE_KEYS = {
    tcod.event.KeySym.UP: (0, -1),  # Mover hacia arriba
    tcod.event.KeySym.W: (0, -1),  # Mover hacia arriba (también con 'w')
    tcod.event.KeySym.DOWN: (0, 1),  # Mover hacia abajo
    tcod.event.KeySym.S: (0, 1),  # Mover hacia abajo (también con 's')
    tcod.event.KeySym.LEFT: (-1, 0),  # Mover hacia la izquierda
    tcod.event.KeySym.A: (-1, 0),  # Mover hacia la izquierda (también con 'a')
    tcod.event.KeySym.RIGHT: (1, 0),  # Mover hacia la derecha
    tcod.event.KeySym.D: (1, 0),  # Mover hacia la derecha (también con 'd')
}

# Tecla para esperar la acción. En este caso, solo la tecla ESPACIO.
WAIT_KEYS = {
    tcod.event.KeySym.SPACE,  # Esperar un turno
}

# Teclas para confirmar una acción (Enter o teclado numérico).
CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,  # Enter
    tcod.event.KeySym.KP_ENTER,  # Enter del teclado numérico
}

# Tipo de retorno que puede ser una acción o un manejador de eventos.
ActionOrHandler = Union[Action, "BaseEventHandler"]
"""
Un valor de retorno de un manejador de eventos que puede disparar una acción o cambiar al siguiente manejador de eventos activo.

Si se retorna un manejador, este será el manejador de eventos activo para los siguientes eventos.
Si se retorna una acción y es válida, se cambia al manejador de eventos principal (MainGameEventHandler).
"""


# Clase base para los manejadores de eventos del juego. Hereda de EventDispatch para despachar eventos.
class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Gestiona un evento y retorna el siguiente manejador de eventos activo."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), (
            f"{self!r} no puede gestionar las acciones."
        )
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        if hasattr(self, "engine"):
            if self.engine.player.is_alive:
                self.engine.save_as("savegame.sav")
            self.engine.message_log.add_message(
                "Partida guardada antes de salir.", color.welcome_text
            )
        raise SystemExit()

    def ev_mousemotion(self, event):
        pass

    def ev_mousebuttondown(self, event):
        pass


# Manejador de eventos que muestra un mensaje emergente (popup).
class PopupMessage(BaseEventHandler):
    """Muestra un mensaje emergente (popup)."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler  # El manejador principal al que se regresará después de mostrar el mensaje.
        self.text = text  # El mensaje a mostrar.

    def on_render(self, console: tcod.Console) -> None:
        """Renderiza el mensaje emergente sobre la pantalla con un fondo atenuado."""
        self.parent.on_render(console)  # Renderiza el estado actual del juego.
        console.rgb["fg"] //= 8  # Atenúa el color de primer plano.
        console.rgb["bg"] //= 8  # Atenúa el color de fondo.

        # Muestra el mensaje centrado en la pantalla.
        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=libtcodpy.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Cualquier tecla regresa al manejador principal."""
        return self.parent


# Manejador de eventos principal del juego, que maneja la interacción del jugador.
class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = (
            engine  # El motor del juego, que contiene la lógica y el estado del juego.
        )

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Guarda la posición del mouse cuando se mueve."""
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = (event.tile.x, event.tile.y)

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Gestiona eventos para los manejadores de entrada con el motor del juego."""
        action_or_state = self.dispatch(event)  # Llama al despachador de eventos
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state  # Si es otro manejador, lo retorna como el nuevo manejador.
        if self.handle_action(action_or_state):  # Si se gestionó una acción válida
            if not self.engine.player.is_alive:  # Si el jugador murió
                return GameOverEventHandler(self.engine)
            elif (
                self.engine.player.level.requires_level_up
            ):  # Si el jugador sube de nivel
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Retorna al manejador principal.
        return self

    def handle_action(self, action: Action) -> bool:
        """Maneja una acción del jugador."""
        if action is not None:
            action.perform()  # Realiza la acción
            self.engine.turn_count += 1  # Incrementa el contador de turnos
            return True
        return False

    def on_render(self, console: tcod.console.Console) -> None:
        """Renderiza el estado actual del juego en la consola."""
        self.engine.render(console)  # Dibuja el estado actual del juego en la consola.


# Manejador de eventos para acciones que requieren una entrada especial del usuario.
class AskUserEventHandler(EventHandler):
    """Gestiona la entrada del usuario para acciones que requieren una entrada especial."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Por defecto, cualquier tecla sale de este manejador de entrada."""
        # Ignorar las teclas modificadoras (Shift, Ctrl, Alt).
        if event.sym in {  # Ignorar las teclas modificadoras.
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None  # No hacer nada si se presionan teclas modificadoras.

        return self.on_exit()  # Si se presiona cualquier otra tecla, salir.

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Por defecto, cualquier clic de ratón sale de este manejador de entrada."""
        return self.on_exit()  # Cualquier clic de ratón sale del manejador.

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Método llamado cuando el usuario intenta salir o cancelar una acción.

        Por defecto, retorna al manejador principal de eventos.
        """
        return MainGameEventHandler(self.engine)  # Retorna al manejador principal.


# Manejador de eventos para mostrar la pantalla de estadísticas del jugador.
class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "        Estadisticas        "

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Llama a la renderización del manejador padre.

        # Determina la posición en el eje X para la ventana.
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 1  # Posición en el eje Y.

        width = len(self.TITLE) + 4  # Ancho de la ventana, considerando el título.

        # Dibuja un marco alrededor de la pantalla de estadísticas.
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=10,  # Altura del marco de estadísticas.
            title=self.TITLE,  # Título de la ventana.
            clear=True,
            fg=(255, 255, 255),  # Color del texto.
            bg=(0, 0, 0),  # Color del fondo.
        )

        # Muestra las estadísticas del jugador.
        console.print(
            x=x + 1, y=y + 1, string=f"Nivel: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP para el proximo nivel: {self.engine.player.level.experience_to_next_level}",
        )
        console.print(
            x=x + 1,
            y=y + 5,
            string=f"Salud: {self.engine.player.fighter.hp}/{self.engine.player.fighter.max_hp}",
        )
        
        # Calcular ataque base y penalización por hambre
        fighter = self.engine.player.fighter
        base_power = fighter.base_power + fighter.power_bonus
        if hasattr(self.engine.player, 'hunger'):
            hunger_state = self.engine.player.hunger.state
            if hunger_state == "weak":
                current_power = int(base_power * 0.75)
                penalty = base_power - current_power
                console.print(
                    x=x + 1, y=y + 6, 
                    string=f"Ataque: {current_power} (-{penalty})"
                )
            elif hunger_state == "moribund":
                current_power = int(base_power * 0.50)
                penalty = base_power - current_power
                console.print(
                    x=x + 1, y=y + 6, 
                    string=f"Ataque: {current_power} (-{penalty})"
                )
            else:
                console.print(
                    x=x + 1, y=y + 6, string=f"Ataque: {base_power}"
                )
        else:
            console.print(
                x=x + 1, y=y + 6, string=f"Ataque: {fighter.power}"
            )
        
        # Calcular defensa base y penalización por efectos temporales o hambre
        base_defense = fighter.base_defense + fighter.defense_bonus
        if hasattr(self.engine.player, 'hunger'):
            hunger_state = self.engine.player.hunger.state
            has_temp_bonus = fighter.temp_defense_bonus > 0
            
            if hunger_state == "weak":
                current_defense = int(base_defense * 0.75)
                penalty = base_defense - current_defense
                console.print(
                    x=x + 1, y=y + 7, 
                    string=f"Defensa: {current_defense} (-{penalty})"
                )
            elif hunger_state == "moribund":
                current_defense = int(base_defense * 0.50)
                penalty = base_defense - current_defense
                console.print(
                    x=x + 1, y=y + 7, 
                    string=f"Defensa: {current_defense} (-{penalty})"
                )
            elif has_temp_bonus:
                current_defense = base_defense + fighter.temp_defense_bonus
                bonus = fighter.temp_defense_bonus
                console.print(
                    x=x + 1, y=y + 7, 
                    string=f"Defensa: {current_defense} (+{bonus})"
                )
            else:
                console.print(
                    x=x + 1, y=y + 7, string=f"Defensa: {base_defense}"
                )
        else:
            if fighter.temp_defense_bonus > 0:
                current_defense = base_defense + fighter.temp_defense_bonus
                bonus = fighter.temp_defense_bonus
                console.print(
                    x=x + 1, y=y + 7, 
                    string=f"Defensa: {current_defense} (+{bonus})"
                )
            else:
                console.print(
                    x=x + 1, y=y + 7, string=f"Defensa: {base_defense}"
                )
        
        # Mostrar hambre si el jugador tiene el componente
        if hasattr(self.engine.player, 'hunger'):
            hunger = self.engine.player.hunger
            hunger_value = hunger.current_hunger
            # Agregar info de estado si no está satisfecho
            if hunger.state != "satisfied":
                state_names = {"hungry": "Hambriento", "weak": "Debil", "moribund": "Moribundo"}
                console.print(
                    x=x + 1, y=y + 8, 
                    string=f"Hambre: {hunger_value} ({state_names[hunger.state]})"
                )
            else:
                console.print(
                    x=x + 1, y=y + 8, string=f"Hambre: {hunger_value}"
                )


# Manejador de eventos para la subida de nivel del jugador.
class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Subida de nivel"  # Título del menú de subida de nivel.

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Llama a la renderización del manejador padre.

        # Determina la posición en el eje X para la ventana.
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        # Dibuja el marco para la ventana de subida de nivel.
        console.draw_frame(
            x=x,
            y=0,
            width=35,  # Ancho de la ventana.
            height=9,  # Altura de la ventana.
            title=self.TITLE,  # Título de la ventana.
            clear=True,
            fg=(255, 255, 255),  # Color del texto.
            bg=(0, 0, 0),  # Color del fondo.
        )

        # Muestra las opciones disponibles para la subida de nivel.
        console.print(x=x + 1, y=1, string="Has subido de nivel.")
        console.print(x=x + 1, y=3, string="Seleccione un atributo a mejorar.")

        console.print(
            x=x + 1,
            y=5,
            string=f"a) Salud (+20 HP)",  # Opción de aumentar salud.
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"b) Fuerza (+1 fuerza)",  # Opción de aumentar fuerza.
        )
        console.print(
            x=x + 1,
            y=7,
            string=f"c) Defensa (+1 defensa)",  # Opción de aumentar defensa.
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player  # Obtiene al jugador.
        key = event.sym  # Obtiene la tecla presionada.
        index = key - tcod.event.KeySym.A  # Calcula el índice (a, b, c).

        if 0 <= index <= 2:  # Verifica si la tecla es válida (a, b o c).
            if index == 0:
                player.level.increase_max_hp()  # Aumenta la salud.
            elif index == 1:
                player.level.increase_power()  # Aumenta la fuerza.
            else:
                player.level.increase_defense()  # Aumenta la defensa.
        else:
            # Si la tecla no es válida, muestra un mensaje de error.
            self.engine.message_log.add_message("Tecla no valida.", color.invalid)
            return None  # No hace nada si la tecla es inválida.

        return super().ev_keydown(event)  # Llama al manejador de eventos padre.

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        No se permite que el jugador haga clic para salir del menú, como normalmente lo haría.
        """
        return None  # Impide que el clic de ratón cierre el menú de subida de nivel.


# Manejador de eventos para gestionar la selección de un ítem en el inventario.
class InventoryEventHandler(AskUserEventHandler):
    """Este manejador permite al usuario seleccionar un item.

    Lo que ocurre después depende de la subclase.
    """

    TITLE = "<missing title>"  # Título del menú de inventario (debe ser definido por las subclases).
    ITEMS_PER_PAGE = 10  # Número de ítems por página

    def __init__(self, *args, **kwargs):
        """Inicializa el manejador de inventario con paginación."""
        super().__init__(*args, **kwargs)
        self.current_page = 0  # Página actual del inventario

    def _get_pagination_info(self):
        """Calcula la información de paginación del inventario."""
        total_items = len(self.engine.player.inventory.items)
        total_pages = max(
            1, (total_items + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        )
        # Asegura que la página actual sea válida
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)
        return total_items, total_pages

    def _get_current_page_items(self):
        """Obtiene los ítems de la página actual."""
        start = self.current_page * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        return self.engine.player.inventory.items[start:end]

    def on_render(self, console: tcod.Console) -> None:
        """Renderiza un menú de inventario paginado.

        Muestra los ítems en páginas de 10, con navegación entre páginas.
        """
        super().on_render(console)  # Llama a la renderización del manejador padre.

        # Obtiene información de paginación
        total_items, total_pages = self._get_pagination_info()
        page_items = self._get_current_page_items()

        # Altura del menú: 10 items máx + indicadores de página + marco
        height = self.ITEMS_PER_PAGE + 4

        if height < 6:
            height = 6  # Altura mínima con navegación

        # Ajusta la posición en X en función de la ubicación del jugador.
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0  # Si el jugador está más a la derecha, el menú se muestra a la izquierda.

        y = 1  # Posición en el eje Y.

        # El ancho del menú se basa en el título más indicador de página
        page_indicator = f" {self.current_page + 1}/{total_pages}"
        width = len(self.TITLE + page_indicator) + 4

        # Dibuja un marco alrededor del menú de inventario.
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,  # Altura del menú.
            title=self.TITLE + page_indicator,  # Título con número de página.
            clear=True,
            fg=(255, 255, 255),  # Color del texto.
            bg=(0, 0, 0),  # Color del fondo.
        )

        # Muestra los ítems de la página actual.
        if total_items > 0:
            for i, item in enumerate(page_items):
                # Calcula el índice real en el inventario (considerando la página)
                real_index = self.current_page * self.ITEMS_PER_PAGE + i
                item_key = chr(ord("a") + real_index)  # Tecla única para cada ítem
                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f"({item_key}) {item.name}"  # String que muestra el ítem.

                if is_equipped:
                    item_string = f"{item_string} (Equipado)"  # Si el ítem está equipado, se indica.

                # Muestra el ítem en la consola.
                console.print(x + 1, y + i + 1, item_string)

            # Muestra controles de navegación si hay más de una página
            if total_pages > 1:
                nav_y = y + self.ITEMS_PER_PAGE + 1
                if self.current_page > 0:
                    console.print(x + 1, nav_y, "<) Pagina anterior", (150, 150, 150))
                if self.current_page < total_pages - 1:
                    console.print(
                        x + width - 14, nav_y, "Pagina sig. >", (150, 150, 150)
                    )
        else:
            console.print(x + 1, y + 1, "(Vacio)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Maneja las teclas para navegar páginas y seleccionar ítems."""
        player = self.engine.player
        key = event.sym
        total_items, total_pages = self._get_pagination_info()

        # Navegación de páginas
        if key == tcod.event.KeySym.COMMA or key == tcod.event.KeySym.COMMA:  # ,
            if self.current_page > 0:
                self.current_page -= 1
            return None

        if key == tcod.event.KeySym.PERIOD or key == tcod.event.KeySym.PERIOD:  # .
            if self.current_page < total_pages - 1:
                self.current_page += 1
            return None

        # Selección de ítems con letras a-z (soporta hasta 26 ítems únicos)
        index = key - tcod.event.KeySym.A

        if (
            0 <= index < total_items
        ):  # Permite cualquier índice válido del inventario total
            try:
                selected_item = player.inventory.items[index]  # Índice real en la lista
            except IndexError:
                self.engine.message_log.add_message("Tecla no valida.", color.invalid)
                return None

            return self.on_item_selected(selected_item)

        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Método llamado cuando el usuario selecciona un ítem válido.

        Este método debe ser implementado por las subclases para gestionar lo que ocurre con el ítem seleccionado.
        """
        raise NotImplementedError()  # La subclase debe implementar este método.


# Manejador de eventos para gestionar el uso de un ítem del inventario.
class InventoryActivateHandler(InventoryEventHandler):
    """Gestiona el uso de un ítem del inventario."""

    TITLE = "   Selecciona un item a usar   "  # Título del menú de uso de ítems.

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Método llamado cuando se selecciona un ítem para usar."""

        # Si el ítem es consumible, obtiene la acción asociada a consumirlo.
        if item.consumable:
            return item.consumable.get_action(self.engine.player)

        # Si el ítem es equipable, devuelve la acción de equiparlo.
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)

        return None  # Si el ítem no es ni consumible ni equipable, no hace nada.


# Manejador de eventos para gestionar el descarte (drop) de un ítem del inventario.
class InventoryDropHandler(InventoryEventHandler):
    """Gestiona el descarte de un ítem del inventario."""

    TITLE = "   Selecciona un item a soltar   "  # Título del menú de descarte de ítems.

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Método llamado cuando se selecciona un ítem para soltar."""

        # Llama a la acción para soltar el ítem seleccionado.
        return actions.DropItem(self.engine.player, item)


# Clase para manejar la selección de un índice en el mapa por parte del jugador.
class SelectIndexHandler(AskUserEventHandler):
    """Maneja la solicitud del usuario para un índice en el mapa."""

    def __init__(self, engine: Engine):
        """Inicializa el manejador y establece el cursor en la posición del jugador."""
        super().__init__(engine)  # Llama al constructor de la clase base.
        player = self.engine.player  # Obtiene al jugador.
        engine.mouse_location = (
            player.x,
            player.y,
        )  # Coloca el cursor en la posición del jugador.

    def on_render(self, console: tcod.console.Console) -> None:
        """Destaca el tile (casilla) bajo el cursor."""
        super().on_render(console)  # Llama al método de renderizado del manejador base.
        x, y = self.engine.mouse_location  # Obtiene la posición del cursor.
        console.rgb["bg"][x, y] = (
            color.white
        )  # Cambia el color de fondo del tile bajo el cursor.
        console.rgb["fg"][x, y] = (
            color.black
        )  # Cambia el color de texto del tile bajo el cursor.

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Maneja la entrada de teclas para mover el cursor o confirmar la selección."""
        key = event.sym  # Obtiene la tecla presionada.

        # Si la tecla es una de las teclas de movimiento, mueve el cursor.
        if key in MOVE_KEYS:
            modifier = 1  # El modificador define la velocidad del movimiento.
            if event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT):
                modifier *= 5  # Si se mantiene Shift, el movimiento es más rápido.
            if event.mod & (tcod.event.Modifier.LCTRL | tcod.event.Modifier.RCTRL):
                modifier *= 10  # Si se mantiene Ctrl, el movimiento es aún más rápido.
            if event.mod & (tcod.event.Modifier.LALT | tcod.event.Modifier.RALT):
                modifier *= 20  # Si se mantiene Alt, el movimiento es muy rápido.

            x, y = self.engine.mouse_location  # Obtiene la ubicación actual del cursor.
            dx, dy = MOVE_KEYS[key]  # Obtiene el desplazamiento de la tecla presionada.
            x += dx * modifier  # Aplica el desplazamiento en el eje X.
            y += dy * modifier  # Aplica el desplazamiento en el eje Y.

            # Restringe el cursor dentro de los límites del mapa.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y  # Actualiza la posición del cursor.
            return None  # No hace nada más si es un movimiento.

        # Si la tecla es una de confirmación, selecciona el índice del cursor.
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)

        return super().ev_keydown(
            event
        )  # Llama al manejador de eventos base si no es ninguna de las anteriores.

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Método llamado cuando se selecciona un índice. Este método debe ser implementado por las subclases."""
        raise NotImplementedError()  # Las subclases deben implementar este método.


# Subclase de SelectIndexHandler que permite al jugador mirar alrededor usando el teclado.
class LookHandler(SelectIndexHandler):
    """Permite al jugador mirar alrededor usando el teclado."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Cuando se selecciona un índice, retorna al manejador principal."""
        return MainGameEventHandler(self.engine)


# Subclase de SelectIndexHandler que maneja el ataque a un solo enemigo. Solo el enemigo seleccionado será afectado.
class SingleRangedAttackHandler(SelectIndexHandler):
    """Maneja el ataque a un solo enemigo. Solo el enemigo seleccionado será afectado."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)  # Inicializa la clase base.
        self.callback = (
            callback  # Guarda la función de callback para ejecutar el ataque.
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """Cuando se selecciona un índice, ejecuta la acción de ataque usando el callback."""
        return self.callback(
            (x, y)
        )  # Llama al callback con las coordenadas seleccionadas.


# Subclase de SelectIndexHandler que maneja el ataque en área dentro de un radio determinado.
class AreaRangedAttackHandler(SelectIndexHandler):
    """Maneja el ataque en un área dentro de un radio dado. Cualquier entidad dentro del área será afectada."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)  # Inicializa la clase base.
        self.radius = radius  # Guarda el radio del área de efecto.
        self.callback = (
            callback  # Guarda la función de callback para ejecutar el ataque en área.
        )

    def on_render(self, console: tcod.console.Console) -> None:
        """Destaca el área de ataque alrededor del cursor."""
        super().on_render(console)  # Llama al método de renderizado del manejador base.

        x, y = self.engine.mouse_location  # Obtiene la ubicación actual del cursor.

        # Dibuja un marco alrededor del área de ataque, para que el jugador vea las casillas afectadas.
        console.draw_frame(
            x=x - self.radius - 1,  # Ajusta la posición en X para centrar el área.
            y=y - self.radius - 1,  # Ajusta la posición en Y para centrar el área.
            width=self.radius**2,  # Calcula el ancho del área de ataque.
            height=self.radius**2,  # Calcula la altura del área de ataque.
            fg=color.red,  # Color del marco de la zona afectada.
            clear=False,  # No limpia el área, solo dibuja el marco.
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """Cuando se selecciona un índice, ejecuta la acción de ataque en área usando el callback."""
        return self.callback(
            (x, y)
        )  # Llama al callback con las coordenadas seleccionadas.


class StairsConfirmationHandler(AskUserEventHandler):
    """Muestra confirmacion antes de bajar las escaleras."""

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        # Atenuar fondo
        console.rgb["fg"] //= 8
        console.rgb["bg"] //= 8

        floor = self.engine.game_world.current_floor
        next_floor = floor + 1

        # Contar habitaciones visitadas / totales
        game_rooms = getattr(self.engine.game_map, 'rooms', [])
        game_visited = getattr(self.engine.game_map, 'visited_rooms', set())
        total_rooms = len(game_rooms)
        visited_rooms = len(game_visited)

        # Contar enemigos vivos (excluyendo al jugador)
        enemies_alive = sum(
            1 for a in self.engine.game_map.actors
            if a is not self.engine.player and a.is_alive
        )

        frame_width = 46
        frame_height = 7
        frame_x = console.width // 2 - frame_width // 2
        frame_y = console.height // 2 - frame_height // 2

        console.draw_frame(
            x=frame_x, y=frame_y,
            width=frame_width, height=frame_height,
            title=" Escaleras ", clear=True,
            fg=color.white, bg=color.black,
        )

        console.print(
            x=frame_x + 1, y=frame_y + 1,
            string=f"Bajar al piso {next_floor}?",
        )

        if total_rooms > 0:
            console.print(
                x=frame_x + 1, y=frame_y + 2,
                string=f"Has visitado {visited_rooms} de {total_rooms} habitaciones.",
                fg=(100, 200, 255),
            )

        if enemies_alive > 0:
            console.print(
                x=frame_x + 1, y=frame_y + 3,
                string=f"Quedan {enemies_alive} enemigos en este piso.",
                fg=(255, 200, 100),
            )

        console.print(
            x=frame_x + 1, y=frame_y + 5,
            string="Enter = Bajar     Otra tecla = Cancelar",
            fg=(150, 150, 150),
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym in CONFIRM_KEYS:
            return actions.TakeStairsAction(self.engine.player)
        return super().ev_keydown(event)


# Clase principal que maneja los eventos del juego mientras está en curso.
class MainGameEventHandler(EventHandler):
    def handle_action(self, action: Optional[Action]) -> bool:
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(str(exc), color.impossible)
            return False

        if self.engine.player.fighter:
            self.engine.player.fighter.on_turn_end()
        
        # Actualizar hambre del jugador
        if hasattr(self.engine.player, 'hunger'):
            self.engine.player.hunger.on_turn_end()

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        self.engine.update_visited_rooms()
        return True

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None  # Inicializa una acción vacía.

        key = event.sym  # Obtiene el símbolo de la tecla presionada.
        modifier = event.mod  # Obtiene los modificadores (como Shift o Ctrl).
        player = self.engine.player  # Obtiene al jugador.

        # Si la tecla presionada corresponde a una de movimiento, ejecuta un movimiento.
        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]  # Obtiene el desplazamiento en X y Y.
            action = BumpAction(
                player, dx, dy
            )  # Crea la acción de movimiento (BumpAction).
        # Si la tecla presionada corresponde a una tecla de espera, ejecuta la acción de espera.
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        # Si se presiona la tecla Escape, regresa al menú principal.
        elif key == tcod.event.KeySym.ESCAPE:
            from core.setup_game import MainMenu

            return MainMenu(self.engine.context, self.engine.console)

        # Modo debugger — F1 abre el menú de debug
        elif key == tcod.event.KeySym.F1:
            from ui.debug_menu import DebugMenuHandler
            return DebugMenuHandler(self.engine)

        # Si se presiona la tecla H, muestra el historial de mensajes.
        elif key == tcod.event.KeySym.H:
            return HistoryViewer(self.engine)

        # Si se presiona la tecla G, el jugador recoge un objeto.
        elif key == tcod.event.KeySym.G:
            action = PickupAction(player)

        # Si se presiona la tecla I, abre la pantalla de inventario para usar un item.
        elif key == tcod.event.KeySym.I:
            return InventoryActivateHandler(self.engine)

        # Si se presiona la tecla F, abre la pantalla de inventario para soltar un item.
        elif key == tcod.event.KeySym.F:
            return InventoryDropHandler(self.engine)

        # Si se presiona la tecla C, abre la pantalla de estadísticas del personaje.
        elif key == tcod.event.KeySym.C:
            return CharacterScreenEventHandler(self.engine)

        # Si se presiona la tecla de barra inclinada (/), permite al jugador mirar alrededor.
        elif key == tcod.event.KeySym.SLASH:
            return LookHandler(self.engine)

        # Si se presiona la tecla E, permite al jugador tomar las escaleras.
        elif key == tcod.event.KeySym.E:
            if (player.x, player.y) == self.engine.game_map.downstairs_location:
                return StairsConfirmationHandler(self.engine)
            self.engine.message_log.add_message(
                "No hay ninguna escalera aqui.", color.impossible
            )
            return None

        # Si ninguna de las teclas válidas fue presionada, retorna la acción asociada (si la hay).
        return action


# Clase que maneja los eventos cuando el juego ha terminado.
class GameOverEventHandler(EventHandler):
    def on_render(self, console: tcod.Console) -> None:
        """Renderiza la pantalla de Game Over con opciones."""
        super().on_render(console)  # Renderiza el estado actual del juego como fondo.

        # Dibuja un marco para el menú de Game Over.
        console.draw_frame(
            x=20,
            y=15,
            width=40,
            height=7,
            title="Fin de la partida",
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        # Muestra las opciones disponibles.
        console.print(x=22, y=17, string="[N] Iniciar nueva partida")
        console.print(x=22, y=18, string="[B] Volver al menu principal")
        console.print(x=22, y=19, string="[Q] Salir del juego")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Maneja las opciones seleccionadas por el jugador."""
        if event.sym == tcod.event.KeySym.N:  # Iniciar nueva partida
            from core.setup_game import new_game

            engine = new_game(
                self.engine.context, self.engine.console
            )  # Pasa el contexto y la consola.
            engine.player.name = (
                self.engine.player.name
            )  # Mantiene el nombre del jugador anterior.
            engine.message_log.add_message(
                f"Bienvenido, {engine.player.name}, a una nueva mazmorra.",
                color.welcome_text,
            )
            return MainGameEventHandler(engine)
        elif event.sym == tcod.event.KeySym.B:  # Volver al menú principal
            from core.setup_game import MainMenu

            return MainMenu(
                self.engine.context, self.engine.console
            )  # Pasa el contexto y la consola.
        elif event.sym == tcod.event.KeySym.Q:  # Salir del juego
            raise exceptions.QuitWithoutSaving()  # Cierra la ventana sin guardar la partida.
        return None


# Diccionario de teclas para mover el cursor hacia arriba o hacia abajo en el historial.
CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,  # Tecla de flecha hacia arriba mueve el cursor hacia arriba.
    tcod.event.KeySym.DOWN: 1,  # Tecla de flecha hacia abajo mueve el cursor hacia abajo.
    tcod.event.KeySym.PAGEUP: -10,  # Página arriba mueve el cursor hacia arriba rápidamente.
    tcod.event.KeySym.PAGEDOWN: 10,  # Página abajo mueve el cursor hacia abajo rápidamente.
}


# Clase que permite al jugador ver el historial de mensajes de manera más grande y desplazarse por él.
class HistoryViewer(EventHandler):
    """Muestra el historial de mensajes en una ventana más grande que se puede navegar."""

    def __init__(self, engine: Engine):
        super().__init__(engine)  # Llama al constructor de la clase base.
        self.log_length = len(
            engine.message_log.messages
        )  # Obtiene la longitud del historial de mensajes.
        self.cursor = self.log_length - 1  # Establece el cursor en el último mensaje.

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)  # Dibuja el estado principal como fondo.

        log_console = tcod.console.Console(
            console.width - 6, console.height - 6
        )  # Crea un área para mostrar el historial.

        # Dibuja un marco con un título personalizado para la ventana de historial.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0,
            0,
            log_console.width,
            1,
            "┤Historial de mensajes├",
            alignment=libtcodpy.CENTER,
        )

        # Dibuja los mensajes del historial en la ventana del historial.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(
            console, 3, 3
        )  # Dibuja la consola del historial en la consola principal.

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        """Maneja el desplazamiento por el historial con las teclas de flecha y otras teclas."""
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]  # Ajusta el movimiento del cursor.
            if adjust < 0 and self.cursor == 0:
                # Si se está en la parte superior, mueve al final del historial.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Si se está en la parte inferior, mueve al inicio del historial.
                self.cursor = 0
            else:
                # Si no está en los bordes, ajusta el cursor dentro de los límites del historial.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0  # Mueve el cursor al principio del historial.
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1  # Mueve el cursor al final del historial.
        else:  # Cualquier otra tecla regresa al manejador principal.
            return MainGameEventHandler(self.engine)
        return None


class GameEventHandler(EventHandler):
    def handle_action(self, action: Optional[Action]) -> None:
        # Verifica si la acción es un BumpAction (intento de moverse a una casilla).
        if isinstance(action, BumpAction):
            target_x, target_y = (
                action.target_x,
                action.target_y,
            )  # Obtiene las coordenadas objetivo.
            tile = self.engine.game_map.tiles[
                target_x, target_y
            ]  # Obtiene el tipo de tile en las coordenadas objetivo.

            # Si el jugador intenta moverse hacia una pared falsa, cambia la acción para revelarla.
            if tile == tile_types.hidden_wall_tile:
                action = RevealHiddenWallAction(self.engine.player, target_x, target_y)

        # Llama al método handle_action de la clase base para procesar la acción.
        super().handle_action(action)
