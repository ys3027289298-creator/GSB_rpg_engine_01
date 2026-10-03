from Character import Character


class CharacterArray:
    def __init__(self):
        self.arr = []

    def __len__(self):
        return len(self.arr)

    def __str__(self):
        returnString = []

        for hero in self.arr:
            returnString.append(str(hero))

        return str(returnString)

    def addCharacter(self, chrctr=None):
        if chrctr is None:
            chrctr = Character("", 0, 0, 0)
        self.arr.append(chrctr)

    def addCharacters(self, CharacterList=None):
        for character in (CharacterList or []):
            self.arr.append(character)

    def get(self, name_key=""):
        for i in range(len(self.arr)):
            if self.arr[i].name.__contains__(name_key):
                return self.arr[i]
        return None

    def at(self, index=0):
        if 0 <= index < len(self.arr):
            return self.arr[index]
        else:
            raise IndexError("Character index {} out of range (length {})".format(index, len(self.arr)))

    def remove(self, name_key=""):
        target = self.get(name_key)
        if target is None:
            raise KeyError("No character found containing {!r}".format(name_key))
        self.arr.remove(target)
