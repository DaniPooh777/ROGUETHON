"""
Este módulo configura el juego, incluyendo la creación de nuevas partidas, carga de partidas guardadas y manejo del menú principal.
Proporciona funciones para inicializar el motor del juego, gestionar el nombre del jugador y realizar transiciones visuales.
"""

from __future__ import annotations  # Asegura compatibilidad con anotaciones de tipo futuras.
from typing import Optional  # Para anotaciones de tipos.
from tcod import console  # Importa la biblioteca tcod para consola y gráficos.
from tcod import libtcodpy  # Importa libtcodpy (funciones de bajo nivel).
from tcod import context  # Maneja el contexto de la consola.
from tcod import console  # Importa la clase Console para manejar la consola de salida.
from engine import Engine  # La clase principal para el motor del juego.
from game_map import GameWorld  # La clase que define el mundo del juego.

import copy  # Para hacer copias profundas de objetos.
import lzma  # Para comprimir y descomprimir datos con el algoritmo LZMA.
import pickle  # Para serializar y deserializar objetos Python.
import traceback  # Para capturar y mostrar rastros de errores.
import time  # Para manejar pausas y temporizadores.
import tcod  # Librería principal para crear roguelikes.
import color  # Módulo personalizado con colores para mensajes.
import entity_factories  # Factores para crear entidades (jugador, objetos, etc.).
import input_handlers  # Gestiona las entradas del usuario.
import exceptions # Maneja excepciones personalizadas.
import sys # Para manejar la ruta del script y el ejecutable.
import os # Para manejar rutas de archivos y directorios.
import color # Para manejar colores personalizados.

# Cambiar la ruta de la imagen de fondo para que sea relativa al directorio del ejecutable o del script
if getattr(sys, 'frozen', False):
    # Si el programa está empaquetado como un ejecutable
    base_path = sys._MEIPASS
else:
    # Si se ejecuta como un script de Python
    base_path = os.path.dirname(__file__)

background_image = tcod.image.load(os.path.join(base_path, "menu_background.png"))[:, :, :3]

# Función para iniciar una nueva partida.
def new_game(context: tcod.context.Context, console: tcod.Console) -> Engine:
    """Retorna una nueva sesión de juego como una instancia de Engine."""
    map_width = 80  # Ancho del mapa.
    map_height = 43  # Alto del mapa.

    # Parámetros para la generación de salas.
    room_max_size = 10
    room_min_size = 6
    max_rooms = 15

    player = copy.deepcopy(entity_factories.player)  # Crea una copia del jugador.

    engine = Engine(player=player, context=context, console=console)  # Pasa el contexto y la consola.

    # Crea el mundo del juego con la configuración.
    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )
    
    # Genera el mapa del mundo y actualiza el FOV.
    engine.game_world.generate_floor()
    engine.update_fov()

    # Crea objetos iniciales (dagger y leather armor).
    dagger = copy.deepcopy(entity_factories.dagger)
    leather_armor = copy.deepcopy(entity_factories.leather_armor)

    # Agrega los objetos al inventario del jugador.
    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    return engine  # Devuelve el motor de juego con todos los elementos inicializados.

# Función para cargar una partida desde un archivo.
def load_game(filename: str, context: tcod.context.Context, console: tcod.Console) -> Engine:
    """Carga una instancia de Engine desde un archivo y restaura el contexto y la consola."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))  # Descomprime y carga el objeto.
    assert isinstance(engine, Engine)  # Asegura que el objeto cargado es una instancia de Engine.

    engine.context = context  # Restaura el contexto.
    engine.console = console  # Restaura la consola.

    return engine  # Devuelve el motor cargado.

# Función para obtener el nombre del jugador (desde un cuadro de texto).
def get_player_name(context: tcod.context.Context, console: tcod.console.Console) -> str:
    name = ""  # Inicializa el nombre vacío.
    screen_width = console.width  # Ancho de la consola.
    screen_height = console.height  # Alto de la consola.
    prompt_text = "Ingresa el nombre de tu personaje (Enter para continuar)"  # Texto de solicitud.
    prompt_x = (screen_width - len(prompt_text)) // 2  # Posición horizontal de la solicitud.
    prompt_y = screen_height // 3  # Posición vertical de la solicitud.
    name_x = screen_width // 2 - 10  # Posición horizontal del cuadro de texto para el nombre.
    name_y = prompt_y + 5  # Posición vertical del cuadro de texto para el nombre.
    name_width = 20  # Ancho del cuadro de texto.

    cursor_visible = True  # Controla la visibilidad del cursor.
    last_blink_time = time.time()  # Marca el tiempo actual.
    blink_interval = 0.5  # Intervalo de parpadeo del cursor.

    while True:  # Bucle para capturar la entrada del nombre.
        current_time = time.time()
        if current_time - last_blink_time > blink_interval:
            cursor_visible = not cursor_visible  # Cambia la visibilidad del cursor.
            last_blink_time = current_time

        console.clear()  # Limpia la consola.
        # Dibuja los marcos alrededor de las áreas de texto.
        console.draw_frame(x=prompt_x - 1, y=prompt_y - 1, width=len(prompt_text) + 2, height=3, title="", clear=True)
        console.draw_frame(x=name_x - 1, y=name_y - 1, width=name_width + 2, height=3, title="", clear=True)
        console.print(prompt_x, prompt_y, prompt_text)  # Dibuja el texto de solicitud.

        # Dibuja el nombre con el cursor que parpadea.
        cursor = "_" if cursor_visible else " "
        display_name = f"{name.ljust(name_width)}"[:name_width]
        if len(name) < name_width:
            display_name = display_name[:len(name)] + cursor + display_name[len(name) + 1:]
        console.print(name_x, name_y, display_name)  # Dibuja el nombre del jugador.

        context.present(console)  # Muestra el contenido de la consola.

        # Captura eventos del teclado.
        for event in tcod.event.get():
            if isinstance(event, tcod.event.Quit):  # Si el jugador sale del juego.
                raise SystemExit()
            elif isinstance(event, tcod.event.KeyDown):  # Si el jugador presiona una tecla.
                if event.sym == tcod.event.KeySym.RETURN:  # Si presiona Enter, retorna el nombre.
                    if name.strip():
                        fade_to_black(console, context)
                        return name
                elif event.sym == tcod.event.KeySym.BACKSPACE:  # Si presiona Backspace, borra un carácter.
                    name = name[:-1]
                    cursor_visible = True
                    last_blink_time = current_time
                elif event.sym == tcod.event.KeySym.SPACE:  # Si se presiona espacio, agrega un espacio al nombre.
                    if len(name) < name_width:
                        name += " "
                elif event.sym == tcod.event.KeySym.ESCAPE:  # Si presiona Escape, cierra el juego.
                    raise SystemExit()
                elif len(event.sym.name) == 1 and event.sym.name.isalpha():  # Si el carácter es una letra, lo agrega al nombre.
                    if len(name) < name_width:
                        char = event.sym.name.lower()
                        if event.mod & tcod.event.Modifier.SHIFT:
                            char = char.upper()
                        name += char

        time.sleep(0.01)  # Pausa para el siguiente ciclo.

# Función para hacer un desvanecimiento a negro en la pantalla.
def fade_to_black(console: tcod.console.Console, context: tcod.context.Context) -> None:
    fade_steps = 10  # Número de pasos de desvanecimiento.
    fade_interval = 0.05  # Intervalo de tiempo entre cada paso de desvanecimiento.
    for step in range(fade_steps):
        intensity = step / fade_steps  # Calcula la intensidad del desvanecimiento.
        console.clear()  # Limpia la consola.
        color = (0, 0, 0)  # Define el color negro.
        # Aplica el desvanecimiento a cada píxel de la consola.
        for y in range(console.height):
            for x in range(console.width):
                console.rgb[x, y] = (
                    int(color[0] * intensity),
                    int(color[1] * intensity),
                    int(color[2] * intensity),
                )
        context.present(console)  # Muestra la consola.
        time.sleep(fade_interval)  # Espera un intervalo antes de continuar.

# Clase para manejar el menú principal del juego.
class MainMenu(input_handlers.BaseEventHandler):
    """Maneja la renderización y entrada del menú principal."""

    def __init__(self, context: tcod.context.Context, console: tcod.Console):
        self.context = context
        self.console = console
        self.last_player_name = None  # Almacena el nombre del jugador de la última partida

    def on_render(self, console: tcod.Console) -> None:
        """Renderiza el menú principal con una imagen de fondo."""
        console.draw_semigraphics(background_image, 0, 0)  # Dibuja la imagen de fondo.

        # Dibuja el título dentro de un rectángulo.
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

        # Dibuja las opciones del menú dentro de otro rectángulo.
        menu_options = [" ", "[N] Nueva partida", "[C] Continuar", "[L] Lenyenda", "[K] Controles", "[Q] Salir", " "]
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

        # Muestra los créditos.
        console.print(
            console.width // 2,
            console.height - 2,
            "Copyright (c) 2025 por DaniPooh",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[input_handlers.BaseEventHandler]:
        """Maneja las entradas del teclado en el menú principal."""
        if event.sym in (tcod.event.KeySym.q, tcod.event.KeySym.ESCAPE):  # Si se presiona Q o Escape, sale del juego.
            raise exceptions.QuitWithoutSaving
        elif event.sym == tcod.event.KeySym.c:  # Si se presiona C, intenta cargar una partida guardada.
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav", self.context, self.console))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No hay una anterior partida guardada.")
            except Exception as exc:
                traceback.print_exc()
                return input_handlers.PopupMessage(self, f"No se ha podido cargar el archivo guardado:\n{exc}")
        elif event.sym == tcod.event.KeySym.n:  # Si se presiona N, empieza una nueva partida.
            fade_to_black(self.console, self.context)  # Fade a negro antes de la transición.

            engine = new_game(self.context, self.console)  # Inicia una nueva partida.
            if self.last_player_name:
                player_name = self.last_player_name  # Usa el nombre de la última partida si existe
            else:
                player_name = get_player_name(self.context, self.console)
            engine.player.name = player_name  # Asigna el nombre al jugador.
            self.last_player_name = player_name  # Guarda el nombre para futuras partidas

            # Muestra un mensaje de bienvenida en el log.
            engine.message_log.add_message(
                f"Bienvenido, {engine.player.name}, a una nueva mazmorra.",
                color.welcome_text
            )

            fade_to_black(self.console, self.context)  # Fade de nuevo antes de entrar al juego.

            handler = input_handlers.MainGameEventHandler(engine)  # Prepara el handler del juego.
            handler.on_render(self.console)  # Renderiza la pantalla de bienvenida.
            self.context.present(self.console)  # Muestra la pantalla.
            time.sleep(1.5)  # Espera un momento para que el jugador vea el mensaje.

            return handler  # Retorna el handler del juego.
        elif event.sym == tcod.event.KeySym.l:
            # Si se presiona L, muestra la leyenda del juego dentro de un marco.
            legend_text = [
                (color.menu_text, "Jugador: @"), 
                (color.player_atk, ""),
                (color.menu_text, "Enemigos:"),
                ((0, 255, 0), " - Goblin: g"),
                ((63, 127, 63), " - Orco: o"),
                ((0, 127, 0), " - Troll: T"), 
                (color.player_atk, ""),
                (color.menu_text, "Objetos:"),
                ((127, 0, 255), " - Pocion de salud: !"),
                ((255, 0, 0), " - Pocion de salud mayor: !"),
                ((207, 63, 255), " - Pergamino de confusion: ~"),
                ((255, 0, 0), " - Pergamino de fuego: ~"),
                ((255, 255, 0), " - Pergamino relampago: ~"),
                ((0, 191, 255), " - Pergamino defensivo: ~"),
                ((128, 128, 255), " - Pergamino invisible: ~"),
                (color.player_atk, ""),
                (color.menu_text, "Equipamiento:"),
                ((0, 191, 255), " - Daga: /"),
                ((105, 105, 105), " - Espada: /"),
                ((139, 69, 19), " - Armadura de cuero: ["),
                ((105, 105, 105), " - Armadura de hierro: ["),
                (color.player_atk, ""),
                ((191, 0, 0), "Cadaver: %"),
                (color.player_atk, ""),
                (color.menu_text, "Paredes: #"),
                (color.player_atk, ""),
                (color.menu_text, "Suelo: ."),
                (color.player_atk, ""),
                (color.menu_text, "Puerta secreta: &"),
                (color.player_atk, ""),
                (color.menu_text, "Escaleras: >"),
            ]

            frame_width = 35
            frame_height = 33
            frame_x = (self.console.width - frame_width) // 2
            frame_y = (self.console.height - frame_height) // 2

            while True:
                # Dibuja el marco en la consola.
                self.console.clear()
                self.console.draw_frame(
                    x=frame_x,
                    y=frame_y,
                    width=frame_width,
                    height=frame_height,
                    title="Leyenda",
                    clear=True,
                    fg=color.menu_text,
                    bg=color.black,
                )

                # Renderizar la leyenda con colores
                for i, (fg, text) in enumerate(legend_text):
                    self.console.print(x=frame_x + 1, y=frame_y + 1 + i, string=text, fg=fg)

                self.context.present(self.console)  # Muestra el contenido de la consola.

                # Captura eventos del teclado.
                for event in tcod.event.wait():
                    if isinstance(event, tcod.event.KeyDown):
                        if event.sym == tcod.event.KeySym.ESCAPE:  # Salir al presionar ESCAPE.
                            return
                        elif event.sym == tcod.event.KeySym.l:  # Salir al presionar ESCAPE.
                            return
        elif event.sym == tcod.event.KeySym.k:
            legend_text = [
                (color.menu_title, "Movimiento:"),
                (color.menu_text, " - Arriba: W o ↑"),
                (color.menu_text, " - Abajo: S o ↓"),
                (color.menu_text, " - Izquierda: A o ←"),
                (color.menu_text, " - Derecha: D o →"), 
                (color.enemy_atk, ""),
                (color.menu_title, "Interaccion:"),
                (color.menu_text, " - Recoger objetos: g"),
                (color.menu_text, " - Soltar objetos: f"),
                (color.menu_text, " - Abrir inventario: i"),
                (color.menu_text, " - Cerrar inventario: Cualquier tecla que"),
                (color.menu_text, "   no sean letras ni el Esc"),
                (color.menu_text, " - Bajar escaleras: e"),
                (color.enemy_atk, ""),
                (color.menu_title, "Combate:"),
                (color.menu_text, " - Atacar: Moverse hacia el enemigo"),
                (color.menu_text, " - Usar objeto: Desde el inventario"),
                (color.enemy_atk, ""),
                (color.menu_title, "Otros controles:"),
                (color.menu_text, " - Salir al menu: Esc"),
                (color.menu_text, " - Confirmar seleccion de objetivo: Enter"),
                (color.menu_text, " - Estadisticas personaje: e"),
                (color.menu_text, " - Mostrar historial: h"),
                (color.menu_text, " - En el historial: ↑ y ↓"),
            ]

            frame_width = 45
            frame_height = 26
            frame_x = (self.console.width - frame_width) // 2
            frame_y = (self.console.height - frame_height) // 2

            while True:
                # Dibuja el marco en la consola.
                self.console.clear()
                self.console.draw_frame(
                    x=frame_x,
                    y=frame_y,
                    width=frame_width,
                    height=frame_height,
                    title="Controles",
                    clear=True,
                    fg=color.menu_text,
                    bg=color.black,
                )

                # Renderizar la leyenda con colores
                for i, (fg, text) in enumerate(legend_text):
                    self.console.print(x=frame_x + 1, y=frame_y + 1 + i, string=text, fg=fg)

                self.context.present(self.console)  # Muestra el contenido de la consola.

                # Captura eventos del teclado.
                for event in tcod.event.wait():
                    if isinstance(event, tcod.event.KeyDown):
                        if event.sym == tcod.event.KeySym.ESCAPE:  # Salir al presionar ESCAPE.
                            return
                        elif event.sym == tcod.event.KeySym.k:  # Salir al presionar k.
                            return
        return None  # No cambia el estado si ninguna tecla es presionada.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        """Maneja el evento de cierre de ventana (clic en la 'X')."""
        raise SystemExit()
