"""
Este módulo define las fábricas de entidades, incluyendo actores (jugadores y enemigos) y objetos (consumibles y equipables).
Cada entidad tiene atributos específicos como IA, equipo, inventario y nivel.
"""

from components.ai import HostileEnemy, RangedEnemy, MimicAI, DragonAI  # AI para enemigos hostiles.
from components import (
    consumable,
    equippable,
)  # Importa componentes de consumibles y equipables.
from components.fighter import Fighter  # Importa la clase Fighter (luchador).
from components.inventory import Inventory  # Importa la clase Inventory (inventario).
from components.hunger import Hunger  # Importa la clase Hunger (hambre).
from entities.entity import Actor, Item  # Importa las clases Actor y Item.
from components.level import Level  # Importa la clase Level (nivel).
from components.equipment import Equipment  # Importa la clase Equipment (equipo).

# Se crea el objeto player, un actor que representa al jugador.
player = Actor(
    char="@",  # Carácter que representa al jugador.
    color=(255, 255, 255),  # Color blanco.
    name="Player",  # Nombre del jugador.
    ai_cls=HostileEnemy,  # Necesario para que is_alive funcione, no se ejecuta en el jugador.
    equipment=Equipment(),  # El jugador tiene equipo vacío por ahora.
    fighter=Fighter(
        hp=30, base_defense=1, base_power=2
    ),  # Atributos de lucha (30 HP, defensa 1, poder 2).
    inventory=Inventory(capacity=26),  # Inventario con capacidad para 26 objetos.
    level=Level(level_up_base=200),  # El jugador sube de nivel al alcanzar 200 XP.
    hunger=Hunger(max_hunger=1000),  # Sistema de hambre del jugador.
)

# Se crean varios enemigos como actores, cada uno con su propia IA y atributos.
orc = Actor(
    char="o",  # Carácter que representa al orco.
    color=(63, 127, 63),  # Color verde.
    name="Orco",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=10, base_defense=0, base_power=4
    ),  # Atributos de lucha (10 HP, defensa 0, poder 4).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=40),  # Da 40 XP al ser derrotado.
)

rata = Actor(
    char="r",  # Carácter que representa a la rata.
    color=(160, 160, 160),  # Color gris.
    name="Rata",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=5, base_defense=0, base_power=2
    ),  # Atributos de lucha (5 HP, defensa 0, poder 2).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=15),  # Da 15 XP al ser derrotado.
)

troll = Actor(
    char="T",  # Carácter que representa al troll.
    color=(0, 127, 0),  # Color verde oscuro.
    name="Troll",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=16, base_defense=1, base_power=5
    ),  # Atributos de lucha (16 HP, defensa 1, poder 5).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=100),  # Da 100 XP al ser derrotado.
)

goblin = Actor(
    char="g",  # Carácter que representa al goblin.
    color=(0, 255, 0),  # Color verde.
    name="Goblin",  # Nombre del enemigo.
    ai_cls=RangedEnemy,  # IA de ataque a distancia.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=8, base_defense=0, base_power=4
    ),  # Atributos de lucha (8 HP, defensa 0, poder 4).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=25),  # Da 25 XP al ser derrotado.
)

# ==================== NUEVOS ENEMIGOS (Ronda 1) ====================

esqueleto = Actor(
    char="s",  # Carácter que representa al esqueleto.
    color=(220, 220, 200),  # Color hueso/blanco.
    name="Esqueleto",  # Nombre del enemigo.
    ai_cls=HostileEnemy,  # IA de enemigo hostil (patrulla y ataca).
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=8, base_defense=0, base_power=3
    ),  # Atributos de lucha (8 HP, defensa 0, poder 3).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=20),  # Da 20 XP al ser derrotado.
)

mimic = Actor(
    char="?",  # Carácter que representa al Mimic (parece cofre).
    color=(160, 120, 60),  # Color marrón (cofre).
    name="Mimic",  # Nombre del enemigo.
    ai_cls=MimicAI,  # IA especial: duerme hasta que el jugador se acerca.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=12, base_defense=1, base_power=6
    ),  # Atributos de lucha (12 HP, defensa 1, poder 6).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=50),  # Da 50 XP al ser derrotado.
)

dragon = Actor(
    char="D",  # Carácter que representa al Dragón.
    color=(255, 50, 50),  # Color rojo fuego.
    name="Dragon",  # Nombre del enemigo.
    ai_cls=DragonAI,  # IA híbrida: cuerpo a cuerpo, fuego, o avanza.
    equipment=Equipment(),  # Equipamiento vacío.
    fighter=Fighter(
        hp=25, base_defense=3, base_power=6
    ),  # Atributos de lucha (25 HP, defensa 3, poder 6).
    inventory=Inventory(capacity=0),  # Inventario vacío.
    level=Level(xp_given=200),  # Da 200 XP al ser derrotado.
)

# Se crean varios ítems, incluyendo pergaminos y pociones consumibles.
confusion_scroll = Item(
    char="~",  # Carácter que representa al pergamino de confusión.
    color=(207, 63, 255),  # Color morado.
    name="Pergamino de la confusion",  # Nombre del objeto.
    consumable=consumable.ConfusionConsumable(
        number_of_turns=10
    ),  # El pergamino causa confusión durante 10 turnos.
)

fireball_scroll = Item(
    char="~",  # Carácter que representa al pergamino de fuego.
    color=(255, 0, 0),  # Color rojo.
    name="Pergamino de fuego",  # Nombre del objeto.
    consumable=consumable.FireballDamageConsumable(
        damage=12, radius=3
    ),  # Causa 12 puntos de daño en un radio de 3.
)

health_potion = Item(
    char="!",  # Carácter que representa la poción de salud.
    color=(127, 0, 255),  # Color púrpura.
    name="Pocion de salud",  # Nombre del objeto.
    consumable=consumable.HealingConsumable(
        amount=5
    ),  # Cura 5 puntos de salud al ser consumida.
)

greater_health_potion = Item(
    char="!",  # Carácter que representa la poción de salud mayor.
    color=(255, 0, 0),  # Color rojo.
    name="Pocion de salud mayor",  # Nombre del objeto.
    consumable=consumable.HealingConsumable(
        amount=10
    ),  # Cura 10 puntos de salud al ser consumida.
)

lightning_scroll = Item(
    char="~",  # Carácter que representa al pergamino de relámpago.
    color=(255, 255, 0),  # Color amarillo.
    name="Pergamino relampago",  # Nombre del objeto.
    consumable=consumable.LightningDamageConsumable(
        damage=20, maximum_range=7
    ),  # Causa 20 puntos de daño a un máximo de 7 casillas.
)

defensive_scroll = Item(
    char="~",  # Carácter que representa al pergamino defensivo.
    color=(0, 191, 255),  # Color azul claro.
    name="Pergamino defensivo",  # Nombre del objeto.
    consumable=consumable.DefensiveScrollConsumable(
        defense_bonus=5, number_of_turns=10
    ),  # Aumenta 5 puntos de defensa durante 10 turnos.
)

invisibility_scroll = Item(
    char="~",  # Carácter que representa al pergamino de invisibilidad.
    color=(128, 128, 255),  # Color azul claro.
    name="Pergamino invisible",  # Nombre del objeto.
    consumable=consumable.InvisibilityScrollConsumable(
        number_of_turns=30
    ),  # Hace al jugador invisible durante 30 turnos.
)

immunity_scroll = Item(
    char="~",  # Carácter que representa al pergamino de inmunidad.
    color=(255, 165, 0),  # Color naranja.
    name="Pergamino de inmunidad",  # Nombre del objeto.
    consumable=consumable.ImmunityScrollConsumable(
        number_of_turns=15
    ),  # Otorga inmunidad total durante 15 turnos.
)

# Se crean objetos equipables, como dagas y armaduras.
dagger = Item(
    char="/",  # Carácter que representa la daga.
    color=(0, 191, 255),  # Color azul claro.
    name="Daga",  # Nombre del objeto.
    equippable=equippable.Dagger(),  # La daga es un objeto equipable.
)

sword = Item(
    char="/",  # Carácter que representa la espada.
    color=(105, 105, 105),  # Color gris oscuro.
    name="Espada",  # Nombre del objeto.
    equippable=equippable.Sword(),  # La espada es un objeto equipable.
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
    color=(105, 105, 105),  # Color gris oscuro.
    name="Armadura de hierro",  # Nombre del objeto.
    equippable=equippable.ChainMail(),  # La cota de malla es un objeto equipable.
)

# ==================== COMIDA ====================

apple = Item(
    char="*",  # Carácter que representa comida.
    color=(255, 100, 100),  # Rojo (manzana).
    name="Manzana",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=80),
)

bread = Item(
    char="-",  # Carácter que representa comida.
    color=(210, 180, 140),  # Marrón (pan).
    name="Pan",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=120),
)

meat = Item(
    char="&",  # Carácter que representa comida.
    color=(139, 69, 19),  # Marrón oscuro (carne).
    name="Carne",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=180),
)

cheese = Item(
    char="=",  # Carácter que representa comida.
    color=(255, 255, 0),  # Amarillo (queso).
    name="Queso",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=100, defense_bonus=1, defense_turns=3),
)

roasted_meat = Item(
    char="%",  # Carácter que representa comida.
    color=(100, 50, 0),  # Marrón oscuro (carne asada).
    name="Carne asada",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=250, power_bonus=2, power_turns=5),
)

soup = Item(
    char="~",  # Carácter que representa comida.
    color=(255, 200, 150),  # Crema (sopa).
    name="Sopa caliente",  # Nombre del objeto.
    consumable=consumable.FoodConsumable(hunger_restore=150, defense_bonus=2, defense_turns=3),
)
