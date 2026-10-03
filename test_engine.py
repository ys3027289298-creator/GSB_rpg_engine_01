import contextlib
import io
import os
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from Character import Character
from CharacterArray import CharacterArray
from Battle import Battle
from FormatText import format_text
from ParseCampaign import Parser
from region import Region


def write_temp_campaign(content):
    handle = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    handle.write(content)
    handle.close()
    return handle.name


class TestParseRecovery(unittest.TestCase):
    def test_empty_path_recovers(self):
        chars, campaign, atmosphere, credits = Parser("").parse_file()
        self.assertEqual(len(chars), 0)
        self.assertEqual(campaign, [])
        self.assertEqual(atmosphere, [])
        self.assertEqual(credits, [])

    def test_missing_file_recovers(self):
        parser = Parser(os.path.join(REPO_DIR, "does", "not", "exist.txt"))
        chars, campaign, atmosphere, credits = parser.parse_file()
        self.assertEqual(len(chars), 0)
        self.assertEqual(campaign, [])

    def test_empty_campaign_file(self):
        path = write_temp_campaign("")
        try:
            chars, campaign, _, _ = Parser(path).parse_file()
            self.assertEqual(len(chars), 0)
            self.assertEqual(campaign, [])
        finally:
            os.unlink(path)

    def test_missing_fields_are_skipped_but_parsing_continues(self):
        path = write_temp_campaign(
            "#Characters\n"
            "Hero: 100 100\n"            # missing block field
            "Villain: abc def ghi\n"     # non-numeric fields
            "NoStats:\n"                 # no fields at all
            "NoColon 5 5 5\n"            # no ': ' separator
            "\n"                         # blank line in character section
            "Survivor: 7 8 9\n"
            "#Campaign\n"
            "The story continues.\n"
        )
        try:
            chars, campaign, _, _ = Parser(path).parse_file()
            self.assertEqual(len(chars), 1)
            self.assertEqual(chars.at(0).name, "Survivor")
            self.assertEqual((chars.at(0).health,
                              chars.at(0).strength,
                              chars.at(0).block), (7, 8, 9))
            self.assertIn("The story continues.\n", campaign)
        finally:
            os.unlink(path)

    def test_campaign_without_character_section(self):
        path = write_temp_campaign("#Campaign\nline one\nline two\n")
        try:
            chars, campaign, _, _ = Parser(path).parse_file()
            self.assertEqual(len(chars), 0)
            self.assertEqual(campaign, ["line one\n", "line two\n"])
        finally:
            os.unlink(path)


class TestCharacterArrayBounds(unittest.TestCase):
    def test_get_and_at_out_of_bounds(self):
        array = CharacterArray()
        self.assertIsNone(array.get("Nobody"))
        self.assertIsNone(array.at(0))
        self.assertIsNone(array.at(-1))

    def test_remove_unknown_is_safe(self):
        array = CharacterArray()
        array.remove("Nobody")
        self.assertEqual(len(array), 0)

    def test_default_character_is_not_shared_between_arrays(self):
        first = CharacterArray()
        second = CharacterArray()
        first.addCharacter()
        second.addCharacter()
        self.assertIsNot(first.at(0), second.at(0))
        first.at(0).health = -999
        self.assertEqual(second.at(0).health, 0)


class TestBattleInvariants(unittest.TestCase):
    def setUp(self):
        self.battle = Battle()
        self.fighter1 = Character("A", 100, 100, 100)
        self.fighter2 = Character("B", 100, 100, 100)

    def test_both_fighters_dead_is_a_draw(self):
        self.fighter1.health = -5
        self.fighter2.health = -5
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.battle.getAttack(self.fighter1, self.fighter2)
        self.assertEqual(result, "End")
        self.assertNotIn("victorious", output.getvalue())
        self.assertIn("fallen", output.getvalue())

    def test_dead_attacker_cannot_act(self):
        self.fighter1.health = 0
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.battle.getAttack(self.fighter1, self.fighter2)
        self.assertEqual(result, "End")
        self.assertEqual(self.fighter2.health, 100)
        self.assertIn("B is victorious!", output.getvalue())

    def test_dead_defender_is_not_attacked(self):
        self.fighter2.health = 0
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.battle.getAttack(self.fighter1, self.fighter2)
        self.assertEqual(result, "End")
        self.assertEqual(self.fighter2.health, 0)
        self.assertIn("A is victorious!", output.getvalue())

    def test_missing_fighters_end_immediately(self):
        self.assertEqual(self.battle.battle(None, self.fighter2), "End")
        self.assertEqual(self.battle.battle(self.fighter1, None), "End")
        self.assertEqual(self.battle.skirmish(None, self.fighter2), "End")

    def test_battle_finishes_with_exactly_one_loser(self):
        random.seed(42)
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            result = self.battle.battle(self.fighter1, self.fighter2)
        self.assertEqual(result, "End")
        dead = [f for f in (self.fighter1, self.fighter2) if f.health <= 0]
        alive = [f for f in (self.fighter1, self.fighter2) if f.health > 0]
        self.assertEqual(len(dead), 1)
        self.assertEqual(len(alive), 1)

    def test_skirmish_with_dead_participant_does_not_damage_survivor(self):
        self.fighter1.health = 0
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            result = self.battle.skirmish(self.fighter1, self.fighter2)
        self.assertEqual(result, "End")
        self.assertEqual(self.fighter2.health, 100)


class TestFormatText(unittest.TestCase):
    def test_empty_line(self):
        self.assertEqual(format_text(""), "")

    def test_empty_colour_segment_does_not_crash(self):
        result = format_text("x [_text256_] y")
        self.assertIn("[_text256_]", result)

    def test_invalid_colour_segment_is_left_intact(self):
        result = format_text("[_text256_abc_]")
        self.assertIn("[_text256_abc_]", result)

    def test_mixed_background_and_text_tokens_on_long_line(self):
        line = "[__background256_10_]BG [_text256_54_]FG"
        result = format_text(line)
        self.assertIn("\u001b[48;5;10m", result)
        self.assertIn("\u001b[38;5;54m", result)

    def test_plain_256_token_keeps_passed_colour(self):
        line = "[_text256_54_]A[reset] then [_text256]B"
        result = format_text(line, colour_code=100)
        self.assertIn("\u001b[38;5;54m", result)
        self.assertIn("\u001b[38;5;100m", result)

    def test_named_codes(self):
        self.assertEqual(format_text("[red]x[reset]"), "\u001b[31mx\u001b[0m")

    def test_long_paragraph_with_many_tokens(self):
        line = " ".join("[_text256_{}_]word{}".format(i, i) for i in range(60))
        result = format_text(line)
        self.assertNotIn("[_text256_", result)
        for i in range(60):
            self.assertIn("\u001b[38;5;{}m".format(i), result)


class TestRegionIsolation(unittest.TestCase):
    def test_characters_are_isolated_between_regions(self):
        first = Region(os.path.join(REPO_DIR, "testParser"))
        second = Region(os.path.join(REPO_DIR, "Ascefelia Campaign", "Ascefelia1"))
        first_ids = {id(character) for character in first.characters.arr}
        second_ids = {id(character) for character in second.characters.arr}
        self.assertTrue(first_ids.isdisjoint(second_ids))

        first.characters.get("Syenite").health = -1
        self.assertEqual(second.characters.get("Fingolfin").health, 100)

    def test_dead_character_cannot_act_in_battle_line(self):
        region = Region(os.path.join(REPO_DIR, "Ascefelia Campaign", "Ascefelia1"))
        region.characters.get("Fingolfin").health = 0
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            result = region.doFunction("battle", format_text(
                "battle => [_text256_81_]Fingolfin[reset], "
                "[_text256_134_]Hollow[reset]"))
        self.assertEqual(result, "End")
        self.assertEqual(region.characters.get("Hollow").health, 80)

    def test_unknown_character_in_battle_line_is_skipped(self):
        region = Region(os.path.join(REPO_DIR, "Ascefelia Campaign", "Ascefelia1"))
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            result = region.doFunction("battle", "battle => Ghost, Hollow")
        self.assertIsNone(result)
        self.assertEqual(region.characters.get("Hollow").health, 80)

    def test_campaign_game_loop_runs_to_battle_end(self):
        random.seed(7)
        region = Region(os.path.join(REPO_DIR, "testParser"))
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            result = region.game_loop()
        self.assertEqual(result, "End")


class TestExampleCampaigns(unittest.TestCase):
    def run_example(self, script, stdin_text):
        env = dict(os.environ)
        env["TERM"] = "xterm"
        completed = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, script)],
            input=stdin_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPO_DIR,
            env=env,
            timeout=120,
            text=True,
        )
        return completed

    def test_fifth_season_example_runs_to_the_end(self):
        completed = self.run_example("The Fifth Season Example.py", "\n" * 10000)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Credits", completed.stdout)

    def test_ascefelia_example_runs_to_the_end(self):
        completed = self.run_example(
            "Ascefelia Example.py", "1\n" * 10000)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Game Over", completed.stdout)


if __name__ == "__main__":
    unittest.main()
