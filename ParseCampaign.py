from Character import Character
from Battle import Battle as Arena
from CharacterArray import CharacterArray
from FormatText import format_text
import sys


class Parser:

    def __init__(self, filepath=""):
        self.filepath = filepath
        self.all_lines = []
        if filepath:
            try:
                with open(filepath, 'r') as campaignfile:
                    self.all_lines = campaignfile.readlines()
            except OSError as error:
                print("Could not open campaign file {!r}: {}".format(filepath, error),
                      file=sys.stderr)
        self.character_dictionary = CharacterArray()
        self.character_section = []
        self.campaign_section = []
        self.atmosphere_section = []
        self.credits_section = []

    @staticmethod
    def split_line(lineIN="", seperator=""):
        partitions = str(lineIN).partition(seperator)
        return str(partitions[0]), str(partitions[2])

    @staticmethod
    def parse_character_stats(Character_line):
        fields = str(Character_line).split()
        if len(fields) != 3:
            raise ValueError("expected 3 stats (health strength block), got {!r}".format(
                Character_line))
        try:
            return [int(fields[0]), int(fields[1]), int(fields[2])]
        except ValueError:
            raise ValueError("non-numeric stats in {!r}".format(Character_line))

    def parse_file(self):
        section = str

        for line in self.all_lines:
            if line.__contains__("#Characters"):
                section = "#Characters"
            elif line.__contains__("#Campaign"):
                section = "#Campaign"
            elif line.__contains__("#Atmosphere"):
                section = "#Atmosphere"
            elif line.__contains__("#Credits"):
                section = "#Credits"

            if section == "#Characters":
                self.character_section.append(format_text(line))
            elif section == "#Campaign":
                self.campaign_section.append(format_text(line))
            elif section == "#Atmosphere":
                self.atmosphere_section.append(format_text(line))
            elif section == "#Credits":
                self.credits_section.append(format_text(line))

        if len(self.character_section) > 0:
            self.character_section.pop(0)
        if len(self.campaign_section) > 0:
            self.campaign_section.pop(0)
        if len(self.atmosphere_section) > 0:
            self.atmosphere_section.pop(0)
        if len(self.credits_section) > 0:
            self.credits_section.pop(0)

        if len(self.character_section) > 0:

            for character in self.character_section:
                if not str(character).strip():
                    continue
                name_key, stats_string = self.split_line(character, ": ")
                try:
                    health, strength, block = self.parse_character_stats(stats_string)
                except ValueError as error:
                    print("Skipping malformed character line: {}".format(error),
                          file=sys.stderr)
                    continue

                New_character = Character(name_key, health, strength, block)
                # print(New_character)
                self.character_dictionary.addCharacter(New_character)

        return self.character_dictionary, self.campaign_section, self.atmosphere_section, self.credits_section

