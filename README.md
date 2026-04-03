# 🎮 ROGUETHON

**ROGUETHON** es un juego de tipo *roguelike* desarrollado en Python, inspirado en los clásicos del género. En este juego, explorarás mazmorras generadas proceduralmente, lutarás contra enemigos, recogerás objetos y mejorarás a tu personaje mientras intentas sobrevivir en un entorno hostil lleno de desafíos.

El juego utiliza la biblioteca [tcod](https://python-tcod.readthedocs.io/) para la creación de gráficos y manejo de eventos, ofreciendo una experiencia visual retro y mecánicas por turnos.

---

## 🖼️ Imágenes del juego

![Captura 1](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%202.png?raw=true)

![Captura 2](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego.png?raw=true)

![Captura 3](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%204.png?raw=true)

![Captura 4](https://github.com/DaniPooh777/ROGUETHON/blob/main/assets/images/Imagen%20juego%203.png?raw=true)

---

## ✨ Nuevas Funcionalidades (v1.0.4)

- **Panel de estados en HUD** — Muestra los efectos activos del jugador (inmunidad, invisibilidad, defensa) y de los enemigos (confusión)
- **Pergamino de inmunidad** — Ahora funciona correctamente, bloqueando todo el daño temporalmente
- **Textos sin tildes** — Sistema de encoding mejorado para evitar problemas visuales

---

## 🎯 Funcionalidades principales

| Categoría | Descripción |
|-----------|-------------|
| **Generación procedural** | Cada partida es única gracias a la creación aleatoria de mapas |
| **Combate por turnos** | Lucha contra enemigos usando armas, hechizos y objetos |
| **Inventario** | Recoge, equipa y usa objetos (armas, armaduras, pociones) |
| **Subida de nivel** | Mejora tus habilidades al ganar experiencia |
| **Habitaciones secretas** | Mazmorras con áreas ocultas por descubrir |
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
| **Pergamino defensivo** | +Defensa temporal |
| **Pergamino invisible** | Invisibilidad temporal |
| **Pergamino de inmunidad** | Invulnerabilidad total temporal |

---

## 🗂️ Estructura del proyecto

```
ROGUETHON/
├── assets/
│   ├── fonts/          # Fuentes del juego
│   └── images/         # Imágenes y capturas
├── build/              # Archivos de compilación
├── components/         # Componentes del juego
│   ├── ai.py          # Inteligencia artificial de enemigos
│   ├── consumable.py  # Objetos consumibles
│   ├── equipment.py   # Sistema de equipamiento
│   ├── fighter.py     # Estadísticas de combate
│   ├── inventory.py   # Gestión de inventario
│   └── level.py       # Sistema de niveles
├── core/              # Núcleo del juego
│   ├── engine.py      # Motor principal
│   ├── game_map.py    # Mapa del juego
│   └── setup_game.py  # Configuración inicial
├── entities/          # Entidades del juego
│   ├── entity.py      # Clase base de entidades
│   └── factories.py   # Fábrcias de entidades
├── systems/           # Sistemas del juego
│   ├── actions.py     # Acciones del jugador
│   ├── procgen.py     # Generación procedural
│   └── rendering.py   # Renderizado
├── ui/                # Interfaz de usuario
│   ├── colors.py      # Colores del juego
│   ├── input_handlers.py  # Manejadores de entrada
│   └── message_log.py    # Registro de mensajes
├── dist/              # Ejecutable compilado
├── saves/             # Partidas guardadas
├── main.py            # Punto de entrada
└── README.md          # Este archivo
```

---

## 🚀 Cómo ejecutar el juego

```bash
# 1. Instalar Python 3.10+ (si no lo tienes)
# 2. Instalar dependencias
pip install tcod

# 3. Clonar el repositorio
git clone https://github.com/DaniPooh777/ROGUETHON.git

# 4. Ejecutar
cd ROGUETHON
cd dist
start ROGUETHON.exe
```

---

*¡Explora las mazmorras, mejora tu personaje y survive al máximo de pisos que puedas!*