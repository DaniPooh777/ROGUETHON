import traceback  # Para imprimir errores en consola.
import tcod  # Librería principal para crear roguelikes.
import color  # Módulo personalizado con colores para mensajes.
import exceptions  # Excepciones personalizadas del juego.
import setup_game  # Configuración inicial del juego.
import input_handlers  # Gestión de entrada y eventos del usuario.
import sys
import os

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
        handler.engine.message_log.add_message("Partida guardada automáticamente.", color.welcome_text)
        print("Partida guardada correctamente.")

# Función principal del juego.
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

        while True:  # Bucle exterior para reiniciar el juego
            handler: input_handlers.BaseEventHandler = setup_game.MainMenu(context, root_console)

            try:
                while True:  # Bucle principal del juego
                    root_console.clear()
                    handler.on_render(console=root_console)
                    context.present(root_console)

                    # Procesar tareas programadas
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
                                        if handler.engine.player.is_alive:
                                            save_game(handler, "savegame.sav")
                                    raise SystemExit()
                                handler = handler.handle_events(event)
                    except Exception:
                        traceback.print_exc()
                        if isinstance(handler, input_handlers.EventHandler):
                            handler.engine.message_log.add_message(
                                traceback.format_exc(), color.error
                            )

            except exceptions.QuitWithoutSaving:
                break  # Salida sin guardar: termina el juego completamente

            except exceptions.PlayerDied:  # Manejar la muerte del jugador.
                if handler.engine.player.is_alive:  # Verifica si el jugador realmente está muerto
                    handler = input_handlers.GameOverEventHandler(handler.engine)
                    continue
            except SystemExit:
                raise  # Asegura que el programa se cierre completamente

            except BaseException:
                raise

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        input("Se produjo un error. Presiona Enter para salir...")
