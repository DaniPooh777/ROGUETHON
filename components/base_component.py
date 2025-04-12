from __future__ import annotations  # Importación de la futura compatibilidad con anotaciones de tipo en clases y métodos.

from typing import TYPE_CHECKING  # Importa TYPE_CHECKING, utilizado para importar clases solo cuando se realiza la comprobación de tipos estáticos.

# Este bloque importa las clases necesarias solo cuando TYPE_CHECKING es verdadero, es decir, solo para la comprobación de tipos estáticos y no en tiempo de ejecución.
if TYPE_CHECKING:
    from engine import Engine  # La clase Engine se importa solo para la comprobación de tipos.
    from entity import Entity  # La clase Entity se importa solo para la comprobación de tipos.
    from game_map import GameMap  # La clase GameMap se importa solo para la comprobación de tipos.


class BaseComponent:
    """Clase base para todos los componentes en el sistema.
    
    Un componente es un objeto que se adjunta a una entidad y le otorga algún tipo de funcionalidad.
    La clase `BaseComponent` se usa como una clase común para todos los componentes, proporcionando acceso a
    la entidad que posee el componente (padre) y funcionalidades comunes como obtener el mapa de juego y el motor.
    """
    
    parent: Entity  # Atributo que almacena la referencia a la entidad que posee este componente. 'parent' es un objeto de la clase `Entity`.

    @property
    def gamemap(self) -> GameMap:
        """Devuelve el mapa de juego en el que se encuentra la entidad.
        
        Este método accede a la propiedad `gamemap` de la entidad padre, lo que proporciona acceso al mapa
        de juego actual. Se define como una propiedad para garantizar que siempre se obtiene el mapa más actualizado.
        """
        return self.parent.gamemap  # Retorna el mapa de juego de la entidad (padre).

    @property
    def engine(self) -> Engine:
        """Devuelve el motor de juego asociado al mapa de juego.
        
        El motor de juego es el sistema central que gestiona la lógica de juego, las actualizaciones y otros procesos
        importantes. Este método accede al motor de juego a través del mapa de juego y lo proporciona como una propiedad.
        """
        return self.gamemap.engine  # Retorna el motor de juego asociado al mapa de juego de la entidad.