import os
from FormatText import format_text


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _prompt():
    try:
        input(">")
    except EOFError:
        pass


class Battle:
    @staticmethod  # used for methods that don't use 'self'  (i think)
    def getAttack(attacker, defender):
        if attacker is None or defender is None:
            return "End"

        if attacker.health <= 0:
            if defender.health <= 0:
                print("Both fighters have fallen!")
            else:
                print("{} is victorious!".format(defender.name))
            return "End"

        if defender.health <= 0:
            print("{} is victorious!".format(attacker.name))
            return "End"

        attack = attacker.attack()
        block = defender.getBlock()
        damage = attack - block
        healthColour = int

        if damage >= 0:
            defender.health -= damage

        if defender.health >= 0.75*defender.maxHealth:
            healthColour = 154
        elif 0.5*defender.maxHealth <= defender.health < 0.75*defender.maxHealth:
            healthColour = 227
        elif 0 < defender.health < 0.5*defender.maxHealth:
            healthColour = 208
        else:
            healthColour = 196

        print(format_text("{} attacked with [red]{}[reset] force!".format(attacker.name, attack)))
        print(format_text("{} blocked with [blue][bold]{}[reset] block!".format(defender.name, block)))
        print(format_text("{}'s health -> [_text256][bold]{}[reset]".format(defender.name, defender.health),
                                                                                             healthColour))
        print()

        if defender.health <= 0:
            print("{} is victorious!".format(attacker.name))
            return "End"
        else:
            return "the fight will continue!"

    def battle(self, fighter1, fighter2):
        if fighter1 is None or fighter2 is None:
            return "End"
        while True:
            if self.getAttack(fighter1, fighter2) == "End":
                return "End"
            _prompt()
            _clear()
            if self.getAttack(fighter2, fighter1) == "End":
                return "End"
            _prompt()
            _clear()

    def skirmish(self, fighter1,  fighter2, rounds=2):
        if fighter1 is None or fighter2 is None:
            return "End"
        for i in range(rounds):
            if i % 2 == 0:
                if self.getAttack(fighter1, fighter2) == "End":
                    return "End"
            else:
                if self.getAttack(fighter2, fighter1) == "End":
                    return "End"
            _prompt()
            _clear()
