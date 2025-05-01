"""
Este módulo gestiona el registro y renderizado de mensajes en el juego.
Proporciona clases para manejar mensajes individuales y un log completo de mensajes.
Los mensajes pueden apilarse si son repetitivos y se renderizan en una región específica de la consola.
"""

from typing import Iterable, List, Reversible, Tuple  # Importaciones necesarias para anotaciones de tipo.

import textwrap  # Se importa para poder ajustar el texto a un ancho determinado.
import tcod  # Importa la biblioteca tcod, que se utiliza para la consola y gráficos del juego.
import color  # Importa un módulo de colores que se utilizará en la visualización de los mensajes.

# Clase que representa un mensaje individual en el log.
class Message:
    def __init__(self, text: str, fg: Tuple[int, int, int]):
        self.plain_text = text  # El texto plano del mensaje.
        self.fg = fg  # El color del texto en formato RGB.
        self.count = 1  # Un contador para saber cuántas veces se repite este mensaje (útil para apilar).

    @property
    def full_text(self) -> str:
        """Devuelve el texto completo del mensaje, incluyendo el contador si es necesario."""
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"  # Si se repite, muestra el contador entre paréntesis.
        return self.plain_text  # Si solo se muestra una vez, solo el texto.

# Clase que maneja el registro y renderizado de los mensajes.
class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []  # Lista para almacenar los mensajes.

    def add_message(
        self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,
    ) -> None:
        """
        Agrega un mensaje al registro de mensajes.

        `text` es el texto del mensaje y `fg` es el color del texto.

        Si `stack` es True, los mensajes iguales se apilarán (su contador aumentará).
        """
        # Si el mensaje puede apilarse (stack es True) y el texto del nuevo mensaje es igual al último,
        # se incrementa el contador del mensaje anterior.
        if stack and self.messages and text == self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, fg))  # Si no, agrega el nuevo mensaje al log.

        # Debugging: Imprime el texto del mensaje para verificar el contenido
        print(f"Mensaje visible: {text}")

    def render(
        self, console: tcod.console.Console, x: int, y: int, width: int, height: int,
    ) -> None:
        """
        Renderiza el log de mensajes sobre la consola.

        `x`, `y`, `width`, `height` es la región rectangular donde se dibujará el log.
        """
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """
        Devuelve el mensaje de texto envuelto para ajustarse al ancho especificado.

        El ajuste de texto se realiza en líneas según el valor de `width`.
        """
        for line in string.splitlines():  # Maneja las nuevas líneas dentro del mensaje.
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )

    @classmethod
    def render_messages(
        cls,
        console: tcod.console.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        """
        Renderiza los mensajes proporcionados, comenzando desde el más reciente.

        Los mensajes se dibujan de atrás hacia adelante, por lo que el mensaje más reciente
        aparecerá en la parte inferior de la consola.
        """
        y_offset = height - 1  # Comienza desde la parte inferior de la región asignada.

        # Recorre los mensajes de atrás hacia adelante.
        for message in reversed(messages):
            # Ajusta el texto del mensaje y lo divide en líneas.
            for line in reversed(list(cls.wrap(message.full_text, width))):
                # Dibuja cada línea en la consola.
                console.print(x=x, y=y + y_offset, string=line, fg=message.fg)
                y_offset -= 1  # Baja la posición para el siguiente mensaje.
                if y_offset < 0:
                    return  # Si no hay más espacio en la consola, termina el renderizado.