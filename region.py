from ParseCampaign import Parser
from Battle import Battle as Arena
from CharacterArray import CharacterArray
import threading
from FormatText import format_text
import Music
import os
import sys


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_input():
    try:
        input(">")
    except EOFError:
        pass


class Region:
    def __init__(self, filepath=""):
        self.region_file = Parser(filepath)
        self.arena = Arena()
        self.keepMusicOn = True
        self.keywords = ['music', 'skirmish', 'battle']
        self.characters = CharacterArray()
        self.characters, self.campaign, self.atmosphere, self.credits = self.region_file.parse_file()

    @staticmethod
    def cleanString(lineIn=""):
        if lineIn.endswith("\n"):
            lineIn = str(lineIn[:len(lineIn) - 1])
        return str(lineIn)

    def hasKeyword(self, lineIN=""):
        for keyword in self.keywords:
            if lineIN.__contains__(keyword):
                return True
        return False

    def getKeyword(self, lineIN=""):
        for keyword in self.keywords:
            if lineIN.__contains__(keyword):
                return keyword
        return -1

    def get_args(self, lineIN=""):
        partitions = self.region_file.split_line(lineIN, " => ")
        fighter1, fighter2 = self.region_file.split_line(str(partitions[1]), ", ")

        return self.cleanString(str(fighter1)), self.cleanString(str(fighter2))

    def get_fighters(self, lineIN=""):
        fighter1_name, fighter2_name = self.get_args(lineIN)
        fighter1 = self.characters.get(fighter1_name)
        fighter2 = self.characters.get(fighter2_name)
        if fighter1 is None or fighter2 is None:
            print("Skipping {!r}: unknown fighter(s) {} / {}".format(
                lineIN.strip(), fighter1_name, fighter2_name), file=sys.stderr)
            return None
        if fighter1.health <= 0 or fighter2.health <= 0:
            return "End"
        return fighter1, fighter2

    def doFunction(self, keyword="", lineIN=""):
        returnValue = None
        if keyword.lower().__contains__("skirmish"):
            fighters = self.get_fighters(lineIN)
            if fighters is None:
                return None
            if fighters == "End":
                return "End"
            returnValue = self.arena.skirmish(fighters[0], fighters[1])

        elif keyword.lower().__contains__("battle"):
            fighters = self.get_fighters(lineIN)
            if fighters is None:
                return None
            if fighters == "End":
                return "End"
            returnValue = self.arena.battle(fighters[0], fighters[1])

        elif keyword.lower().__contains__("music"):
            partitions = self.region_file.split_line(lineIN, " => ")
            music_thread = threading.Thread(target=Music.play_song, args=(self.cleanString(partitions[1]),))
            music_thread.start()
            clear()

        return returnValue

    def game_loop(self):
        returnValue = None
        if len(self.atmosphere) > 0:
            for line in self.atmosphere:
                if self.hasKeyword(str(line)):
                    self.doFunction(self.getKeyword(line), line)
        clear()

        if len(self.campaign) > 0:
            for line in self.campaign:
                if self.hasKeyword(str(line)):
                    returnValue = self.doFunction(self.getKeyword(line), line)
                    wait_for_input()
                    clear()
                else:
                    if str(line) != "\n":
                        print(self.cleanString(line))
                    else:
                        wait_for_input()
                        clear()

        self.keepMusicOn = False

        if len(self.credits) > 0:
            clear()
            print("Credits:")
            for credit in self.credits:
                print(credit)
            wait_for_input()

        return returnValue
