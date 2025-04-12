# Importación de las clases necesarias desde otros módulos.
from components.ai import HostileEnemy  # AI para enemigos hostiles.
from components import consumable, equippable  # Importa componentes de consumibles y equipables.
from components.fighter import Fighter  # Importa la clase Fighter (luchador).
from components.inventory import Inventory  # Importa la clase Inventory (inventario).
from entity import Actor, Item  # Importa las clases Actor y Item.
from components.level import Level  # Importa la clase Level (nivel).
from components.equipment import Equipment  # Importa la clase Equipment (equipo).

# Se crea el objeto player, un actor que representa al jugador.
player = Actor(
    char="@",  # Carácter que representa al jugador.
    color=(255, 255, 255),  # Color blanco.
    name="Player",  # Nombre del jugador.
    ai_cls=HostileEnemy,  # Asigna una clase de IA para enemigo hostil.
    equipment=Equipment(),  # El jugador tiene equipo vacío por ahora.
    fighter=Fighter(hp=30, base_defense=1, base_power=2),  # Atributos de lucha (30 HP, defensa 1, poder 2).
    inventory=Inventory(capacity=26),  # Inventario con capacidad para 26 objetos.
    level=Level(level_up_base=200),  # El jugador sube de nivel al alcanzar 200 XP.
)

# Se crean varios enemigos como actores, cada uno con su propia IA y atributos.
orc = Actor(
    char="o",  # Carácter que representa al orco.
    color=(63, 127, 63),  # Color verde.
    name="Orco",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(hp=10, base_defense=0, base_power=3),  # Atributos de lucha (10 HP, defensa 0, poder 3).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=35),  # Da 35 XP al ser derrotado.
)

troll = Actor(
    char="T",  # Carácter que representa al troll.
    color=(0, 127, 0),  # Color verde oscuro.
    name="Troll",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(hp=16, base_defense=1, base_power=4),  # Atributos de lucha (16 HP, defensa 1, poder 4).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=100),  # Da 100 XP al ser derrotado.
)

# Se crean varios ítems, incluyendo pergaminos y pociones consumibles.
confusion_scroll = Item(
    char="~",  # Carácter que representa al pergamino de confusión.
    color=(207, 63, 255),  # Color morado.
    name="Pergamino de la confusion",  # Nombre del objeto.
    consumable=consumable.ConfusionConsumable(number_of_turns=10),  # El pergamino causa confusión durante 10 turnos.
)

fireball_scroll = Item(
    char="~",  # Carácter que representa al pergamino de fuego.
    color=(255, 0, 0),  # Color rojo.
    name="Pergamino de fuego",  # Nombre del objeto.
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),  # Causa 12 puntos de daño en un radio de 3.
)

health_potion = Item(
    char="!",  # Carácter que representa la poción de salud.
    color=(127, 0, 255),  # Color púrpura.
    name="Pocion de salud",  # Nombre del objeto.
    consumable=consumable.HealingConsumable(amount=4),  # Cura 4 puntos de salud al ser consumida.
)

lightning_scroll = Item(
    char="~",  # Carácter que representa al pergamino de relámpago.
    color=(255, 255, 0),  # Color amarillo.
    name="Pergamino relampago",  # Nombre del objeto.
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=3),  # Causa 20 puntos de daño a un máximo de 3 casillas.
)

# Se crean objetos equipables, como dagas y armaduras.
dagger = Item(
    char="/",  # Carácter que representa la daga.
    color=(0, 191, 255),  # Color azul claro.
    name="Daga",  # Nombre del objeto.
    equippable=equippable.Dagger()  # La daga es un objeto equipable.
)

sword = Item(
    char="/",  # Carácter que representa la espada.
    color=(0, 191, 255),  # Color azul claro.
    name="Espada",  # Nombre del objeto.
    equippable=equippable.Sword()  # La espada es un objeto equipable.
)

# Se crean armaduras equipables.
leather_armor = Item(
    char="[",  # Carácter que representa la armadura de cuero.
    color=(139, 69, 19),  # Color marrón.
    name="Armadura de cuero",  # Nombre del objeto.
    equippable=equippable.LeatherArmor(),  # La armadura de cuero es un objeto equipable.
)

chain_mail = Item(
    char="[",  # Carácter que representa la cota de malla.
    color=(139, 69, 19),  # Color marrón.
    name="Armadura de cota de malla",  # Nombre del objeto.
    equippable=equippable.ChainMail()  # La cota de malla es un objeto equipable.
)