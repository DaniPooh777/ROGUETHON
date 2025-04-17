# ROGUETHON

**ROGUETHON** es un juego de tipo *roguelike* desarrollado en Python, inspirado en los clásicos del género. En este juego, explorarás mazmorras generadas proceduralmente, lucharás contra enemigos, recogerás objetos y mejorarás a tu personaje mientras intentas sobrevivir en un entorno hostil lleno de desafíos.

El juego utiliza la biblioteca [tcod](https://python-tcod.readthedocs.io/) para la creación de gráficos y manejo de eventos, ofreciendo una experiencia visual retro y mecánicas por turnos.

## Funcionalidades principales

- **Generación procedural de mazmorras**: Cada partida es única gracias a la creación aleatoria de mapas.
- **Sistema de combate por turnos**: Lucha contra enemigos utilizando armas, hechizos y objetos consumibles.
- **Inventario y equipo**: Recoge, equipa y utiliza objetos como armas, armaduras y pociones.
- **Subida de nivel**: Mejora las habilidades de tu personaje a medida que ganas experiencia.
- **Registro de mensajes**: Un sistema de registro que muestra eventos importantes durante el juego.
- **Gráficos retro**: Estilo visual basado en tilesets clásicos.

## Controles del juego

A continuación, se detallan los controles básicos para jugar a **ROGUETHON**:

### Movimiento
- **Teclas de dirección `(↑,  ↓,  ←,  →)`**: Mover al personaje en las direcciones correspondientes.
- **Teclas `(w, a, s, d)`**: Mover al personaje en las direcciones correspondientes.

### Interacción
- **Tecla `g`**: Recoger objetos del suelo.
- **Tecla `i`**: Abrir el inventario.
- **Tecla `f`**: Soltar un objeto del inventario.
- **Tecla `e`**: Para acceder a las escaleras.

### Combate
- Moverse hacia un enemigo para atacarlo cuerpo a cuerpo.
- Usar objetos consumibles (como pociones) desde el inventario.

### Otros controles
- **Tecla `Esc`**: Salir del juego.
- **Tecla `Enter`**: Confirmar selecciones en menús.
- **Tecla `h`**: Mostrar el historial de acciones del jugador.
- **Tecla `c`**: Mostrar las estadísticas del personaje.
- **Tecla `(↑,  ↓)`**: En el historial de acciones del jugador para moverse arriba y abajo a lo largo de todos los mensajes.

## Cómo ejecutar el juego

1. Asegúrate de tener Python 3.10 o superior instalado.
2. Instala las dependencias necesarias ejecutando:
   ```bash
   pip install tcod