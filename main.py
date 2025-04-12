import traceback  # Para imprimir errores en consola.
import tcod  # Librería principal para crear roguelikes.
import color  # Módulo personalizado con colores para mensajes.
import exceptions  # Excepciones personalizadas del juego.
import setup_game  # Configuración inicial del juego.
import input_handlers  # Gestión de entrada y eventos del usuario.

# Función para guardar la partida actual.
def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """Si el handler actual tiene un Engine activo, guarda la partida."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)  # Guarda el estado del juego en un archivo.
        print("Partida guardada.")  # Mensaje en consola (útil para debug).

# Función principal del juego.
def main() -> None:
    screen_width = 80  # Ancho de la pantalla en caracteres.
    screen_height = 50  # Alto de la pantalla en caracteres.

    # Carga la hoja de tiles (fuente gráfica) para mostrar caracteres.
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    # Crea el contexto de la ventana con el tileset y configuración.
    with tcod.context.new(
        columns = screen_width,
        rows = screen_height,
        tileset = tileset,
        title = "ROGUETHON",  # Título de la ventana.
        vsync = True,  # Sincroniza con la frecuencia de actualización del monitor.
    ) as context:
        # Crea la consola raíz que se usará para renderizar.
        root_console = tcod.console.Console(screen_width, screen_height, order="F")

        # Crea el handler del menú principal, pasándole el contexto y la consola.
        handler: input_handlers.BaseEventHandler = setup_game.MainMenu(context, root_console)

        try:
            while True:  # Bucle principal del juego.
                root_console.clear()  # Limpia la consola antes de dibujar.
                handler.on_render(console=root_console)  # Dibuja usando el handler actual.
                context.present(root_console)  # Presenta lo dibujado en pantalla.

                try:
                    for event in tcod.event.wait():  # Espera a eventos del usuario (teclado, mouse).
                        context.convert_event(event)  # Convierte eventos a formato tcod.
                        handler = handler.handle_events(event)  # Maneja el evento y puede cambiar de handler.
                except Exception:  # Si ocurre un error durante el manejo de eventos...
                    traceback.print_exc()  # Imprime el error completo en consola.
                    if isinstance(handler, input_handlers.EventHandler):
                        # También muestra el error en el registro de mensajes del juego.
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            # Excepción específica para salir sin guardar (por ejemplo, desde el menú).
            raise
        except SystemExit:  # Si se cierra el juego normalmente (por ejemplo, pulsando salir).
            save_game(handler, "savegame.sav")  # Guarda la partida antes de salir.
            raise
        except BaseException:  # Cualquier otro error inesperado.
            save_game(handler, "savegame.sav")  # Guarda antes de salir por precaución.
            raise

if __name__ == "__main__":
    main()
