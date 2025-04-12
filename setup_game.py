from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional
from tcod import console

import time
import tcod
from tcod import libtcodpy  # Importa libtcodpy

import color
from engine import Engine
import entity_factories
import input_handlers
from game_map import GameWorld


# Load the background image and remove the alpha channel.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )
    
    engine.game_world.generate_floor()
    engine.update_fov()

    dagger = copy.deepcopy(entity_factories.dagger)
    leather_armor = copy.deepcopy(entity_factories.leather_armor)

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    return engine


def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

def get_player_name(context: tcod.context.Context, console: tcod.console.Console) -> str:
    name = ""
    screen_width = console.width
    screen_height = console.height
    prompt_text = "Ingresa el nombre de tu personaje (Enter para continuar)"
    prompt_x = (screen_width - len(prompt_text)) // 2
    prompt_y = screen_height // 3
    name_x = screen_width // 2 - 10
    name_y = prompt_y + 5
    name_width = 20

    cursor_visible = True
    last_blink_time = time.time()
    blink_interval = 0.5

    while True:
        current_time = time.time()
        if current_time - last_blink_time > blink_interval:
            cursor_visible = not cursor_visible
            last_blink_time = current_time

        console.clear()
        console.draw_frame(x=prompt_x - 1, y=prompt_y - 1, width=len(prompt_text) + 2, height=3, title="", clear=True)
        console.draw_frame(x=name_x - 1, y=name_y - 1, width=name_width + 2, height=3, title="", clear=True)
        console.print(prompt_x, prompt_y, prompt_text)

        cursor = "_" if cursor_visible else " "
        display_name = f"{name.ljust(name_width)}"[:name_width]
        if len(name) < name_width:
            display_name = display_name[:len(name)] + cursor + display_name[len(name) + 1:]
        console.print(name_x, name_y, display_name)
        context.present(console)

        for event in tcod.event.get():
            if isinstance(event, tcod.event.Quit):
                raise SystemExit()
            elif isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.KeySym.RETURN:
                    return name if name else "Link"
                elif event.sym == tcod.event.KeySym.BACKSPACE:
                    name = name[:-1]
                    cursor_visible = True
                    last_blink_time = current_time
                elif event.sym == tcod.event.KeySym.ESCAPE:
                    raise SystemExit()
                elif event.sym == tcod.event.KeySym.MINUS and (event.mod & tcod.event.Modifier.SHIFT):
                    if len(name) < name_width:
                        name += "_"
                        cursor_visible = True
                        last_blink_time = current_time
                else:
                    char = event.sym.name
                    is_shift = (event.mod & tcod.event.Modifier.SHIFT)
                    if len(char) == 1 and char.isprintable():
                        char = char.upper() if is_shift else char.lower()
                        if len(name) < name_width:
                            name += char
                            cursor_visible = True
                            last_blink_time = current_time
                    elif char == "space":
                        if len(name) < name_width:
                            name += " "
                            cursor_visible = True
                            last_blink_time = current_time
        time.sleep(0.01)


def fade_to_black(console: tcod.console.Console, context: tcod.context.Context) -> None:
    fade_steps = 10
    fade_interval = 0.05
    for step in range(fade_steps):
        intensity = step / fade_steps
        console.clear()
        color = (0, 0, 0)
        for y in range(console.height):
            for x in range(console.width):
                console.rgb[x, y] = (
                    int(color[0] * intensity),
                    int(color[1] * intensity),
                    int(color[2] * intensity),
                )
        context.present(console)
        time.sleep(fade_interval)


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def __init__(self, context: tcod.context.Context, console: tcod.Console):
        self.context = context
        self.console = console

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        # Título grande dentro de un rectángulo
        title_text = "ROGUETHON "
        title_width = len(title_text) + 3
        title_x = (console.width - title_width) // 2
        title_y = console.height // 2 - 8

        console.draw_frame(
            x=title_x,
            y=title_y,
            width=title_width,
            height=5,
            title="",
            clear=False,
            fg=color.menu_title,
            bg=color.black,
        )

        console.print(
            console.width // 2,
            title_y + 2,
            title_text,
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )

        # Opciones dentro de otro rectángulo
        menu_options = [" ", "[N] Nueva partida", "[C] Continuar", "[Q] Salir", " "]
        menu_width = 24
        menu_x = (console.width - menu_width) // 2
        menu_y = console.height // 2 - 2

        console.draw_frame(
            x=menu_x - 2,
            y=menu_y - 1,
            width=menu_width + 3,
            height=len(menu_options) + 2,
            title="",
            clear=False,
            fg=color.menu_text,
            bg=color.black,
        )

        for i, text in enumerate(menu_options):
            console.print(
                console.width // 2,
                menu_y + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )

        # Créditos
        console.print(
            console.width // 2,
            console.height - 2,
            "POR DANIPOOH",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )


    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.KeySym.c:
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No hay una anterior partida guardada.")
            except Exception as exc:
                traceback.print_exc()
                return input_handlers.PopupMessage(self, f"No se ha podido cargar el archivo guardado:\n{exc}")
        elif event.sym == tcod.event.KeySym.n:
            # Fade to black before transitioning to name entry
            fade_to_black(self.console, self.context)

            engine = new_game()
            player_name = get_player_name(self.context, self.console)
            engine.player.name = player_name

            # Añadir mensaje de bienvenida personalizado al log
            engine.message_log.add_message(
                f"Bienvenido, {engine.player.name}, a una nueva mazmorra.",
                color.welcome_text
            )

            # Fade de nuevo antes de entrar al juego
            fade_to_black(self.console, self.context)

            # Mostrar mensaje de bienvenida al arrancar el handler
            handler = input_handlers.MainGameEventHandler(engine)
            handler.on_render(self.console)  # Renderiza la pantalla con el mensaje
            self.context.present(self.console)
            time.sleep(1.5)  # Espera un momento para que el jugador vea el mensaje

            return handler

        return None