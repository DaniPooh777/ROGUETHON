# Definición de una excepción personalizada llamada Impossible.
class Impossible(Exception):
    """Excepción que se lanza cuando una acción es imposible de realizar.

    La razón por la que la acción es imposible se proporciona como mensaje de la excepción.
    """
    # Esta clase simplemente extiende la clase base Exception. No tiene funcionalidad adicional
    # más allá de almacenar el mensaje de error que se pasa al momento de lanzar la excepción.

# Definición de una excepción personalizada llamada QuitWithoutSaving.
class QuitWithoutSaving(SystemExit):
    """Excepción que se puede lanzar para salir del juego sin guardar automáticamente."""
    # Esta clase extiende la excepción SystemExit para salir del programa, pero no guarda el estado.
    # Esto es útil en situaciones donde, por ejemplo, un jugador decide salir del juego sin querer guardar
    # el progreso actual. Al extender SystemExit, asegura que el programa se termine correctamente.

class PlayerDied(SystemExit):
    """Excepción que se lanza cuando el jugador muere.

    Esta excepción se utiliza para indicar que el jugador ha muerto y el juego debe terminar.
    """
    # Esta clase extiende SystemExit para salir del programa, indicando que el jugador ha muerto.
    # Se puede usar para manejar la lógica de finalización del juego o mostrar un mensaje de muerte al jugador.