from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod
import libtcodpy

import actions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item


# Diccionario que asocia las teclas de dirección a los movimientos en el mapa.
# Cada tecla de dirección corresponde a un desplazamiento en el eje X o Y.
MOVE_KEYS = {
    tcod.event.KeySym.UP: (0, -1),  # Mover hacia arriba
    tcod.event.KeySym.w: (0, -1),   # Mover hacia arriba (también con 'w')
    tcod.event.KeySym.DOWN: (0, 1),  # Mover hacia abajo
    tcod.event.KeySym.s: (0, 1),    # Mover hacia abajo (también con 's')
    tcod.event.KeySym.LEFT: (-1, 0), # Mover hacia la izquierda
    tcod.event.KeySym.a: (-1, 0),   # Mover hacia la izquierda (también con 'a')
    tcod.event.KeySym.RIGHT: (1, 0),# Mover hacia la derecha
    tcod.event.KeySym.d: (1, 0),    # Mover hacia la derecha (también con 'd')
}

# Tecla para esperar la acción. En este caso, solo la tecla ESPACIO.
WAIT_KEYS = {
    tcod.event.KeySym.SPACE,
}

# Teclas para confirmar una acción (Enter o teclado numérico).
CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,
    tcod.event.KeySym.KP_ENTER,
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
        state = self.dispatch(event)  # Llama al despachador de eventos para obtener el estado
        if isinstance(state, BaseEventHandler):
            return state  # Si el estado es otro manejador, lo retorna como el nuevo manejador activo.
        assert not isinstance(state, Action), f"{self!r} no puede gestionar las acciones."
        return self  # Si no es un manejador, retorna el manejador actual.

    def on_render(self, console: tcod.Console) -> None:
        """Método abstracto que debe ser implementado por los manejadores específicos."""
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        """Manejador de eventos cuando el juego solicita salir."""
        raise SystemExit()  # Sale del juego.


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
        self.engine = engine  # El motor del juego, que contiene la lógica y el estado del juego.

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Gestiona eventos para los manejadores de entrada con el motor del juego."""
        action_or_state = self.dispatch(event)  # Llama al despachador de eventos
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state  # Si es otro manejador, lo retorna como el nuevo manejador.
        if self.handle_action(action_or_state):  # Si se gestionó una acción válida
            if not self.engine.player.is_alive:  # Si el jugador murió
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:  # Si el jugador sube de nivel
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Retorna al manejador principal.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Gestiona las acciones devueltas por los métodos de eventos.

        Retorna True si la acción avanza un turno.
        """
        if action is None:
            return False  # Si no hay acción, no avanza el turno.

        try:
            action.perform()  # Realiza la acción.
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Si ocurre una excepción (acción imposible), no avanza el turno.

        self.engine.handle_enemy_turns()  # Permite que los enemigos actúen.

        self.engine.update_fov()  # Actualiza el campo de visión del jugador.
        return True  # La acción fue válida y el turno avanzó.

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Actualiza la ubicación del ratón si está dentro de los límites del mapa."""
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y  # Actualiza la ubicación del ratón.

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

        y = 0  # Posición en el eje Y.

        width = len(self.TITLE) + 4  # Ancho de la ventana, considerando el título.

        # Dibuja un marco alrededor de la pantalla de estadísticas.
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,  # Altura del marco de estadísticas.
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
            x=x + 1, y=y + 4, string=f"Ataque: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defensa: {self.engine.player.fighter.defense}"
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
        index = key - tcod.event.K_a  # Calcula el índice (a, b, c).

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

    def on_render(self, console: tcod.Console) -> None:
        """Renderiza un menú de inventario, que muestra los ítems en el inventario y la letra para seleccionarlos.

        La posición del menú se ajusta según la ubicación del jugador, para que siempre esté visible.
        """
        super().on_render(console)  # Llama a la renderización del manejador padre.
        
        # Obtiene el número de ítems en el inventario del jugador.
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2  # Altura del menú basada en el número de ítems.
        
        if height <= 3:
            height = 3  # Asegura que el menú tenga al menos 3 líneas de altura.

        # Ajusta la posición en X en función de la ubicación del jugador.
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0  # Si el jugador está más a la derecha, el menú se muestra a la izquierda.

        y = 0  # Posición en el eje Y.

        # El ancho del menú se basa en el título del menú.
        width = len(self.TITLE) + 4

        # Dibuja un marco alrededor del menú de inventario.
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,  # Altura del menú.
            title=self.TITLE,  # Título del menú.
            clear=True,
            fg=(255, 255, 255),  # Color del texto.
            bg=(0, 0, 0),  # Color del fondo.
        )

        # Si hay ítems en el inventario, los muestra.
        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)  # La tecla asociada al ítem (a, b, c...).
                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f"({item_key}) {item.name}"  # String que muestra el ítem.

                if is_equipped:
                    item_string = f"{item_string} (Equipado)"  # Si el ítem está equipado, se indica.

                # Muestra el ítem en la consola.
                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x + 1, y + 1, "(Vacio)")  # Si no hay ítems, muestra un mensaje indicando que está vacío.

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player  # Obtiene al jugador.
        key = event.sym  # Obtiene la tecla presionada.
        index = key - tcod.event.KeySym.a  # Calcula el índice del ítem seleccionado (a, b, c...).

        # Verifica que la tecla presionada corresponda a un ítem válido en el inventario (índice de 0 a 26).
        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]  # Obtiene el ítem seleccionado.
            except IndexError:
                # Si la tecla presionada está fuera del rango, muestra un mensaje de error.
                self.engine.message_log.add_message("Tecla no valida.", color.invalid)
                return None  # No hace nada si la tecla es inválida.
            
            # Llama al método correspondiente para gestionar la selección del ítem.
            return self.on_item_selected(selected_item)
        
        return super().ev_keydown(event)  # Llama al manejador de eventos padre si la tecla no es válida.

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
        engine.mouse_location = player.x, player.y  # Coloca el cursor en la posición del jugador.

    def on_render(self, console: tcod.console.Console) -> None:
        """Destaca el tile (casilla) bajo el cursor."""
        super().on_render(console)  # Llama al método de renderizado del manejador base.
        x, y = self.engine.mouse_location  # Obtiene la posición del cursor.
        console.rgb["bg"][x, y] = color.white  # Cambia el color de fondo del tile bajo el cursor.
        console.rgb["fg"][x, y] = color.black  # Cambia el color de texto del tile bajo el cursor.

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

        return super().ev_keydown(event)  # Llama al manejador de eventos base si no es ninguna de las anteriores.

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Confirma la selección con un clic izquierdo del ratón."""
        if self.engine.game_map.in_bounds(*event.tile):  # Verifica que el clic esté dentro de los límites del mapa.
            if event.button == 1:  # Si el botón presionado es el izquierdo.
                return self.on_index_selected(*event.tile)  # Llama al método de selección con las coordenadas del clic.
        return super().ev_mousebuttondown(event)  # Llama al manejador de eventos base si no es un clic válido.

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
        self.callback = callback  # Guarda la función de callback para ejecutar el ataque.

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """Cuando se selecciona un índice, ejecuta la acción de ataque usando el callback."""
        return self.callback((x, y))  # Llama al callback con las coordenadas seleccionadas.


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
        self.callback = callback  # Guarda la función de callback para ejecutar el ataque en área.

    def on_render(self, console: tcod.console.Console) -> None:
        """Destaca el área de ataque alrededor del cursor."""
        super().on_render(console)  # Llama al método de renderizado del manejador base.

        x, y = self.engine.mouse_location  # Obtiene la ubicación actual del cursor.

        # Dibuja un marco alrededor del área de ataque, para que el jugador vea las casillas afectadas.
        console.draw_frame(
            x=x - self.radius - 1,  # Ajusta la posición en X para centrar el área.
            y=y - self.radius - 1,  # Ajusta la posición en Y para centrar el área.
            width=self.radius ** 2,  # Calcula el ancho del área de ataque.
            height=self.radius ** 2,  # Calcula la altura del área de ataque.
            fg=color.red,  # Color del marco de la zona afectada.
            clear=False,  # No limpia el área, solo dibuja el marco.
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        """Cuando se selecciona un índice, ejecuta la acción de ataque en área usando el callback."""
        return self.callback((x, y))  # Llama al callback con las coordenadas seleccionadas.

# Clase principal que maneja los eventos del juego mientras está en curso.
class MainGameEventHandler(EventHandler):
    def handle_action(self, action: Optional[Action]) -> bool:
        """Ejecuta una acción y maneja el final del turno."""
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(str(exc), color.impossible)
            return False  # No termina el turno si la acción es imposible.

        # Llama a on_turn_end para el jugador.
        if self.engine.player.fighter:
            self.engine.player.fighter.on_turn_end()

        self.engine.handle_enemy_turns()  # Maneja los turnos de los enemigos.
        self.engine.update_fov()  # Actualiza el campo de visión.
        return True

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None  # Inicializa una acción vacía.

        key = event.sym  # Obtiene el símbolo de la tecla presionada.
        modifier = event.mod  # Obtiene los modificadores (como Shift o Ctrl).
        player = self.engine.player  # Obtiene al jugador.

        # Si la tecla presionada corresponde a una de movimiento, ejecuta un movimiento.
        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]  # Obtiene el desplazamiento en X y Y.
            action = BumpAction(player, dx, dy)  # Crea la acción de movimiento (BumpAction).
        # Si la tecla presionada corresponde a una tecla de espera, ejecuta la acción de espera.
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        # Si se presiona la tecla Escape, termina el juego.
        elif key == tcod.event.KeySym.ESCAPE:
            raise SystemExit()
        # Si se presiona la tecla H, muestra el historial de mensajes.
        elif key == tcod.event.KeySym.h:
            return HistoryViewer(self.engine)

        # Si se presiona la tecla G, el jugador recoge un objeto.
        elif key == tcod.event.KeySym.g:
            action = PickupAction(player)

        # Si se presiona la tecla I, abre la pantalla de inventario para usar un item.
        elif key == tcod.event.KeySym.i:
            return InventoryActivateHandler(self.engine)
        
        # Si se presiona la tecla F, abre la pantalla de inventario para soltar un item.
        elif key == tcod.event.KeySym.f:
            return InventoryDropHandler(self.engine)
        
        # Si se presiona la tecla C, abre la pantalla de estadísticas del personaje.
        elif key == tcod.event.KeySym.c:
            return CharacterScreenEventHandler(self.engine)
        
        # Si se presiona la tecla de barra inclinada (/), permite al jugador mirar alrededor.
        elif key == tcod.event.KeySym.SLASH:
            return LookHandler(self.engine)

        # Si se presiona la tecla E, permite al jugador tomar las escaleras.
        elif key == tcod.event.KeySym.e:
            return actions.TakeStairsAction(player)

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
        if event.sym == tcod.event.KeySym.n:  # Iniciar nueva partida
            from setup_game import new_game
            engine = new_game(self.engine.context, self.engine.console)  # Pasa el contexto y la consola.
            return MainGameEventHandler(engine)
        elif event.sym == tcod.event.KeySym.b:  # Volver al menú principal
            from setup_game import MainMenu
            return MainMenu(self.engine.context, self.engine.console)  # Pasa el contexto y la consola.
        elif event.sym == tcod.event.KeySym.q:  # Salir del juego
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
        self.log_length = len(engine.message_log.messages)  # Obtiene la longitud del historial de mensajes.
        self.cursor = self.log_length - 1  # Establece el cursor en el último mensaje.

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)  # Dibuja el estado principal como fondo.

        log_console = tcod.console.Console(console.width - 6, console.height - 6)  # Crea un área para mostrar el historial.

        # Dibuja un marco con un título personalizado para la ventana de historial.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Historial de mensajes├", alignment=libtcodpy.CENTER
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
        log_console.blit(console, 3, 3)  # Dibuja la consola del historial en la consola principal.

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