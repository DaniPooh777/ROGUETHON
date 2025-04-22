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
        handler.engine.save_as(filename)  # Guarda el estado del motor del juego
        print("Partida guardada correctamente.") # Añade un mensaje en la terminal notificando que la partida fue guardada (para debug)

# Función principal del juego, donde se configura la pantalla y el bucle de juego.
def main() -> None:
    screen_width = 80  # Ancho de la ventana del juego en tiles.
    screen_height = 50  # Alto de la ventana del juego en tiles.

    # Carga el tileset desde el archivo.
    tileset = tcod.tileset.load_tilesheet(tileset_path, 32, 8, tcod.tileset.CHARMAP_TCOD)

    # Crea un contexto gráfico para manejar la ventana del juego.
    with tcod.context.new(
        columns=screen_width,  # Número de columnas (ancho).
        rows=screen_height,  # Número de filas (alto).
        tileset=tileset,  # Los tiles gráficos del juego.
        title="ROGUETHON",  # El título de la ventana.
        vsync=True,  # Habilita la sincronización vertical para evitar "tearing".
    ) as context:
        # Crea la consola donde se dibujará el juego.
        root_console = tcod.console.Console(screen_width, screen_height, order="F")

        while True:  # Bucle externo para reiniciar el juego tras la muerte o salida al menú.
            handler: input_handlers.BaseEventHandler = setup_game.MainMenu(context, root_console)  # Llama al menú principal.

            try:
                while True:  # Bucle principal del juego.
                    root_console.clear()  # Limpia la consola en cada iteración.
                    handler.on_render(console=root_console)  # Renderiza el estado actual del juego en la consola.
                    context.present(root_console)  # Muestra la consola renderizada en pantalla.

                    # Procesa las tareas programadas (como efectos temporales o movimientos automáticos).
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.process_scheduled_tasks()

                    try:
                        for event in tcod.event.wait():  # Espera eventos del usuario (teclado, clics, etc.).
                            context.convert_event(event)  # Convierte el evento al formato adecuado para el contexto gráfico.
                            if isinstance(event, tcod.event.Quit):  # Si el evento es salir del juego (cerrar ventana).
                                if isinstance(handler, input_handlers.EventHandler):
                                    if handler.engine.player.is_alive:  # Si el jugador está vivo, guarda el progreso.
                                        save_game(handler, "savegame.sav")
                                raise SystemExit()  # Sale del juego.

                            if isinstance(event, tcod.event.KeyDown):  # Si se presiona una tecla.
                                if event.sym == tcod.event.KeySym.ESCAPE:  # Si se presiona ESC.
                                    if isinstance(handler, input_handlers.EventHandler):
                                        if handler.engine.player.is_alive:  # Si el jugador está vivo, guarda el progreso.
                                            save_game(handler, "savegame.sav")
                                    raise SystemExit()  # Sale del juego.

                                handler = handler.handle_events(event)  # Procesa el evento (moverse, atacar, etc.).

                    except Exception:  # Si ocurre una excepción en el bucle de eventos.
                        traceback.print_exc()  # Muestra el error completo en consola.
                        if isinstance(handler, input_handlers.EventHandler):
                            # Añade el error al registro de mensajes en el juego.
                            handler.engine.message_log.add_message(
                                traceback.format_exc(), color.error
                            )

            except exceptions.QuitWithoutSaving:  # Si se sale sin guardar la partida.
                break  # Termina el juego.

            except exceptions.PlayerDied:  # Si el jugador muere.
                if handler.engine.player.is_alive:  # Verifica si el jugador está realmente muerto.
                    handler = input_handlers.GameOverEventHandler(handler.engine)  # Cambia al estado de "Game Over".
                    continue  # Vuelve al bucle principal para mostrar la pantalla de derrota.

            except SystemExit:  # Si se lanza una excepción para cerrar el juego (SystemExit).
                raise  # Vuelve a lanzar la excepción para terminar el programa.

            except BaseException:  # Captura cualquier otro tipo de error crítico.
                raise  # Lanza la excepción para detener la ejecución.

# Punto de entrada del script, que llama a la función principal y maneja excepciones globales.
if __name__ == "__main__":
    try:
        main()  # Llama a la función principal del juego.
    except exceptions.Impossible as exc:  # Si ocurre un error que indica una acción imposible en el juego.
        print(f"Error capturado: {exc}")  # Muestra el error en consola.
        input("Presiona Enter para salir...")  # Espera al usuario para cerrar.
    except Exception:  # Captura cualquier otro error no esperado.
        traceback.print_exc()  # Muestra el error completo en consola.
        input("Se produjo un error. Presiona Enter para salir...")  # Espera al usuario para cerrar.
