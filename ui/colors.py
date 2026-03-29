"""
Este módulo define una paleta de colores en formato RGB (Rojo, Verde, Azul) para ser utilizados en diferentes aspectos del juego.
Incluye colores básicos, colores relacionados con acciones, muertes, errores, texto, barras y menús.
"""

# Colores básicos
white = (0xFF, 0xFF, 0xFF)  # Blanco
black = (0x0, 0x0, 0x0)     # Negro
red = (0xFF, 0x0, 0x0)      # Rojo

# Colores relacionados con las acciones del jugador y enemigos
player_atk = (0xE0, 0xE0, 0xE0)  # Ataque del jugador (gris claro)
enemy_atk = (0xFF, 0xC0, 0xC0)   # Ataque del enemigo (rojo claro)
needs_target = (0x3F, 0xFF, 0xFF)  # Necesita un objetivo (azul claro)
status_effect_applied = (0x3F, 0xFF, 0x3F)  # Efecto de estado aplicado (verde claro)
descend = (0x9F, 0x3F, 0xFF)  # Descender a un nuevo nivel (azul oscuro)
invisibility_applied = (128, 128, 255)  # Color azul claro para el efecto de invisibilidad.

# Colores relacionados con las muertes
player_die = (0xFF, 0x30, 0x30)  # Muerte del jugador (rojo brillante)
enemy_die = (0xFF, 0xA0, 0x30)  # Muerte del enemigo (amarillo anaranjado)

# Colores para situaciones de error o imposible
invalid = (0xFF, 0xFF, 0x00)  # Acción inválida (amarillo)
impossible = (0x80, 0x80, 0x80)  # Acción imposible (gris)
error = (0xFF, 0x40, 0x40)  # Error (rojo fuerte)

# Colores de texto y recuperaciones
welcome_text = (0x20, 0xA0, 0xFF)  # Texto de bienvenida (azul claro)
health_recovered = (0x0, 0xFF, 0x0)  # Salud recuperada (verde brillante)

# Colores de barra (por ejemplo, para mostrar la salud del jugador)
bar_text = white  # Texto de la barra (blanco)
bar_filled = (0x0, 0x60, 0x0)  # Barra llena (verde oscuro)
bar_empty = (0x40, 0x10, 0x10)  # Barra vacía (rojo oscuro)

# Colores de menú
menu_title = (255, 255, 63)  # Título del menú (amarillo claro)
menu_text = white  # Texto del menú (blanco)