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
- **Tecla `Espace`**: Pasar el turno.
- **Tecla `h`**: Mostrar el historial de acciones del jugador.
- **Tecla `c`**: Mostrar las estadísticas del personaje.
- **Tecla `(↑,  ↓)`**: En el historial de acciones del jugador para moverse arriba y abajo a lo largo de todos los mensajes.

## Enemigos

En **ROGUETHON**, te enfrentarás a una variedad de enemigos, cada uno con habilidades y comportamientos únicos. Algunos ejemplos incluyen:

- **Orcos**: Enemigos básicos con ataques cuerpo a cuerpo.
- **Trolls**: Criaturas más fuertes con alta salud y poder de ataque.
- **Goblins**: Enemigos rápidos que atacan a distancia.

Cada enemigo tiene fortalezas y debilidades que deberás aprender para enfrentarlos de manera efectiva.

## Objetos consumibles

Durante tu aventura, encontrarás diversos objetos consumibles que te ayudarán a sobrevivir:

- **Poción de salud**: Restaura puntos de vida.
- **Pergamino de confusión**: Confunde a un enemigo, haciéndolo moverse aleatoriamente durante varios turnos.
- **Pergamino de relámpago**: Lanza un rayo que inflige daño al enemigo más cercano.
- **Pergamino de bola de fuego**: Causa daño en un área, afectando a múltiples enemigos.
- **Pergamino defensivo**: Aumenta temporalmente tu defensa, reduciendo el daño recibido.
- **Pergamino invisible**: El jugador se vuelve temporalmente invisible para los enemigos.

Usa estos objetos estratégicamente para superar los desafíos de las mazmorras.

## Imágenes del juego

A continuación, se incluyen capturas de pantalla del juego para mostrar su estilo visual y mecánicas:

![Captura de pantalla 1](https://github.com/DaniPooh777/ROGUETHON/blob/main/Imagen%20juego%202.png?raw=true)
<br/><br/>
![Captura de pantalla 2](https://github.com/DaniPooh777/ROGUETHON/blob/main/Imagen%20juego.png?raw=true)

## Cómo ejecutar el juego

1. Asegúrate de tener Python 3.10 o superior instalado.
2. Instala las dependencias necesarias en el Símbolo del Sistema ejecutando:
   ```bash
   pip install tcod
   ```
3. Clona el repositorio con:
   ```bash
   git clone https://github.com/DaniPooh777/ROGUETHON.git
   ```
4. Accede a la carpeta con:
   ```bash
   cd ROGUETHON
   ```
5. Ejecuta el juego con:
   ```
   start ROGUETHON.exe.lnk
   ```
###Y ahora disfruta del juego.
