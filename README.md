# 🎮 ROGUETHON

**ROGUETHON** es un juego de tipo *roguelike* desarrollado en Python, inspirado en los clásicos del género. En este juego, explorarás mazmorras generadas proceduralmente, lutarás contra enemigos, recogerás objetos y mejorarás a tu personaje mientras intentas sobrevivir en un entorno hostil lleno de desafíos.

El juego utiliza la biblioteca [tcod](https://python-tcod.readthedocs.io/) para la creación de gráficos y manejo de eventos, ofreciendo una experiencia visual retro y mecánicas por turnos.

---

## 🎯 Funcionalidades principales

| Categoría | Descripción |
|-----------|-------------|
| **Generación procedural** | Cada partida es única gracias a la creación aleatoria de mapas |
| **Variedad de habitaciones** | Habitaciones rectangulares, circulares, en L y en T |
| **Habitaciones secretas** | Áreas ocultas que aparecen aleatoriamente |
| **Combate por turnos** | Lucha contra enemigos usando armas, hechizos y objetos |
| **Inventario** | Recoge, equipa y usa objetos (armas, armaduras, pociones) |
| **Subida de nivel** | Mejora tus habilidades al ganar experiencia |
| **Mouse tooltip** | Muestra el nombre de entidades al pasar el mouse |
| **Registro de mensajes** | Historial de eventos importantes del juego |

---

## ⌨️ Controles del juego

### Movimiento
| Tecla | Acción |
|-------|--------|
| `↑, ↓, ←, →` | Mover al personaje |
| `w, a, s, d` | Mover al personaje (alternativo) |
| `Espacio` | Pasar el turno |

### Interacción
| Tecla | Acción |
|-------|--------|
| `g` | Recoger objetos del suelo |
| `i` | Abrir/cerrar inventario |
| `f` | Soltar un objeto |
| `e` | Bajar por las escaleras |

### Otros
| Tecla | Acción |
|-------|--------|
| `Esc` | Salir del juego |
| `Enter` | Confirmar selección |
| `c` | Estadísticas del personaje |
| `h` | Historial de acciones |

---

## 👾 Enemigos

En **ROGUETHON**, te enfrentarás a una variedad de enemigos únicos:

- **Orcos** — Enemigos básicos con ataques cuerpo a cuerpo
- **Trolls** — Criaturas fuertes con alta salud y poder de ataque
- **Goblins** — Enemigos rápidos que atacan a distancia

---

## 🧪 Objetos consumibles

| Objeto | Efecto |
|--------|--------|
| **Poción de salud** | Restaura 5 puntos de vida |
| **Poción de salud mayor** | Restaura 10 puntos de vida |
| **Pergamino de confusión** | Confunde al enemigo por varios turnos |
| **Pergamino de relámpago** | Daño al enemigo más cercano |
| **Pergamino de bola de fuego** | Daño en área a múltiples enemigos |
| **Pergamino defensivo** | + Defensa temporal |
| **Pergamino invisible** | Invisibilidad temporal |
| **Pergamino de inmunidad** | Invulnerabilidad total temporal |

---

## 🖼️ Imágenes del juego

![Captura 1](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego.png?raw=true)

![Captura 2](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%202.png?raw=true)

![Captura 3](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%203.png?raw=true)

![Captura 4](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%204.png?raw=true)

---

## 🗂️ Estructura del proyecto

```
ROGUETHON/
├── main.py            # Punto de entrada
├── README.md          # Este archivo
├── .gitignore         # Archivos ignorados por Git
├── main.spec          # Configuración de PyInstaller
├── menu_background.png # Imagen de fondo del menú
├── savegame.sav       # Partida guardada
├── assets/
│   ├── fonts/
│   └── images/
├── build/
├── components/
│   ├── ai.py
│   ├── base_component.py
│   ├── consumable.py
│   ├── equipment.py
│   ├── equippable.py
│   ├── fighter.py
│   ├── inventory.py
│   └── level.py
├── core/
│   ├── engine.py
│   ├── exceptions.py
│   ├── game_map.py
│   ├── setup_game.py
│   └── tile_types.py
├── dist/              # Ejecutable compilado
├── entities/
│   ├── entity.py
│   └── factories.py
├── saves/             # Partidas guardadas
├── systems/
│   ├── actions.py
│   ├── procgen.py
│   └── rendering.py
└── ui/
    ├── colors.py
    ├── equipment_types.py
    ├── input_handlers.py
    ├── message_log.py
    └── render_order.py
```

---

## 🚀 Cómo ejecutar el juego

1. Asegúrate de tener Python 3.10 o superior instalado.
2. Descarga Git para poder clonar el código:
   [Pulsa aquí](https://git-scm.com/downloads/win)
4. Instala las dependencias necesarias en el Símbolo del Sistema ejecutando:
   ```bash
   pip install tcod
   ```
5. Clona el repositorio con:
   ```bash
   git clone https://github.com/DaniPooh777/ROGUETHON.git
   ```
6. Accede a la carpeta con:
   ```bash
   cd ROGUETHON
   ```
7. Accede a esta parpeta:
   ```bash
   cd dist
   ```
8. Ejecuta el juego con:
   ```
   start ROGUETHON.exe
   ```

---

*¡Explora las mazmorras, mejora tu personaje y sobrevive al máximo de pisos que puedas!*
