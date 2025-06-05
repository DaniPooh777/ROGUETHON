"""
Este es el archivo principal de ejecución del juego 'ROGUETHON'.
Se encarga de iniciar la interfaz gráfica con `tcod`, mostrar el menú principal,
manejar eventos del usuario y controlar el ciclo de vida del juego,
incluyendo la carga, guardado y manejo de errores y excepciones.
"""

import traceback  # Para imprimir errores en consola.
import tcod  # Librería principal para crear roguelikes.
import color  # Módulo personalizado con colores para mensajes.
import exceptions  # Excepciones personalizadas del juego.
import setup_game  # Configuración inicial del juego.
import input_handlers  # Gestión de entrada y eventos del usuario.
import sys  # Proporciona acceso a variables y funciones del sistema, como el estado del intérprete o argumentos de línea de comandos.
import os  # Permite interactuar con el sistema operativo, por ejemplo, para manejar rutas y archivos.

from tcod import libtcodpy

# Cambiar la ruta del tileset para que sea relativa al directorio del ejecutable o del script
if getattr(sys, 'frozen', False):
    # Si el programa está empaquetado como un ejecutable
    base_path = sys._MEIPASS
else:
    # Si se ejecuta como un script de Python
    base_path = os.path.dirname(__file__)

tileset_path = os.path.join(base_path, "dejavu10x10_gs_tc.png")

# Función para guardar la partida actual.
def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """Guarda el estado del juego en un archivo si el handler tiene un Engine activo."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Partida guardada correctamente.")

# Función principal del juego, donde se configura la pantalla y el bucle de juego.
def main() -> None:
    screen_width = 80
    screen_height = 50

    tileset = tcod.tileset.load_tilesheet(tileset_path, 32, 8, tcod.tileset.CHARMAP_TCOD)

    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="ROGUETHON",
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order="F")

        # Oculta el cursor del ratón siempre
        libtcodpy.mouse_show_cursor(False)

        while True:
            handler: input_handlers.BaseEventHandler = setup_game.MainMenu(context, root_console)

            try:
                while True:
                    root_console.clear()
                    handler.on_render(console=root_console)
                    context.present(root_console)

                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.process_scheduled_tasks()

                    try:
                        for event in tcod.event.wait():
                            context.convert_event(event)
                            if isinstance(event, tcod.event.Quit):
                                if isinstance(handler, input_handlers.EventHandler):
                                    if handler.engine.player.is_alive:
                                        save_game(handler, "savegame.sav")
                                raise SystemExit()

                            if isinstance(event, tcod.event.KeyDown):
                                if event.sym == tcod.event.KeySym.ESCAPE:
                                    if isinstance(handler, input_handlers.EventHandler):
                                        from setup_game import MainMenu
                                        save_game(handler, "savegame.sav")
                                        handler = MainMenu(context, root_console)
                                        break
                                handler = handler.handle_events(event)

                    except Exception:
                        traceback.print_exc()
                        if isinstance(handler, input_handlers.EventHandler):
                            handler.engine.message_log.add_message(
                                traceback.format_exc(), color.error
                            )

            except exceptions.QuitWithoutSaving:
                break

            except exceptions.PlayerDied:
                if handler.engine.player.is_alive:
                    handler = input_handlers.GameOverEventHandler(handler.engine)
                    continue

            except SystemExit:
                raise

            except BaseException:
                raise

# Punto de entrada del script, que llama a la función principal y maneja excepciones globales.
if __name__ == "__main__":
    try:
        main()
    except exceptions.Impossible as exc:
        print(f"Error capturado: {exc}")
        input("Presiona Enter para salir...")
    except Exception:
        traceback.print_exc()
        input("Se produjo un error. Presiona Enter para salir...")
