from typing import Tuple  # Importa el tipo Tuple de typing para anotaciones de tipos.

import numpy as np  # type: ignore  # Importa la librería numpy, ignorando el chequeo de tipos.

# Definición del tipo estructurado para los gráficos de un tile, compatible con Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # "ch" almacena el código Unicode del carácter para el tile.
        ("fg", "3B"),  # "fg" es un array de 3 bytes (RGB) que representa el color del primer plano.
        ("bg", "3B"),  # "bg" es un array de 3 bytes (RGB) que representa el color de fondo.
    ]
)

# Definición del tipo estructurado para un tile completo, incluyendo atributos como walkable y transparent.
tile_dt = np.dtype(
    [
        ("walkable", bool),  # "walkable" es un booleano que indica si el tile es accesible.
        ("transparent", bool),  # "transparent" es un booleano que indica si el tile es transparente para el FOV.
        ("dark", graphic_dt),  # "dark" contiene los gráficos cuando el tile está fuera del FOV (sin luz).
        ("light", graphic_dt),  # "light" contiene los gráficos cuando el tile está en el FOV (con luz).
    ]
)

# Función auxiliar para definir nuevos tipos de tiles.
def new_tile(
    *,  # Se utiliza "*" para obligar a usar nombres de parámetros (palabras clave) al llamar a la función.
    walkable: int,  # Indica si el tile es caminable.
    transparent: int,  # Indica si el tile es transparente en cuanto a FOV.
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],  # Gráficos para el tile en la oscuridad (fuera del FOV).
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],  # Gráficos para el tile iluminado (dentro del FOV).
) -> np.ndarray:
    """Función auxiliar para definir tipos de tiles individuales."""
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)  # Retorna un array con los datos de un tile.

# SHROUD representa los tiles no explorados (no vistos por el jugador).
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Definición del tile de suelo (floor)
floor = new_tile(
    walkable=True,  # El suelo es caminable.
    transparent=True,  # El suelo es transparente para el FOV.
    dark=(ord("."), (100, 100, 100), (0, 0, 0)),  # Representación en oscuridad (fuera del FOV).
    light=(ord("."), (200, 200, 200), (0, 0, 0)),  # Representación con luz (dentro del FOV).
)

# Definición del tile de pared (wall)
wall = new_tile(
    walkable=False,  # Las paredes no son caminables.
    transparent=False,  # Las paredes no son transparentes para el FOV.
    dark=(ord("#"), (100, 100, 100), (0, 0, 0)),  # Representación en oscuridad (fuera del FOV).
    light=(ord("#"), (200, 200, 200), (0, 0, 0)),  # Representación con luz (dentro del FOV).
)

# Definición del tile de escaleras hacia abajo (down_stairs)
down_stairs = new_tile(
    walkable=True,  # Las escaleras son caminables.
    transparent=True,  # Las escaleras son transparentes para el FOV.
    dark=(ord(">"), (100, 100, 100), (0, 0, 0)),  # Representación en oscuridad (fuera del FOV).
    light=(ord(">"), (200, 200, 200), (0, 0, 0)),  # Representación con luz (dentro del FOV).
)

door = new_tile(
    walkable=True,
    transparent=False,
    dark=(ord("&"), (100, 100, 100), (0, 0, 0)),
    light=(ord("&"), (200, 200, 200), (0, 0, 0)),
)
