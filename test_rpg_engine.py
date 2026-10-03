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
sys.path.insert(0, REPO_DIR)

from Battle import Battle
from Character import Character
from CharacterArray import CharacterArray
from FormatText import format_text
from ParseCampaign import Parser
from region import Region


def write_campaign(text):
    fd, path = tempfile.mkstemp(suffix=".campaign")
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    return path


CAMPAIGN_TWO_FIGHTERS = (
    "#Characters\n"
    "Alpha: 100 50 10\n"
    "Beta: 100 50 10\n"
    "#Campaign\n"
    "battle => Alpha, Beta\n"
)


class TestParseFailureRecovery(unittest.TestCase):
    def test_empty_filepath_raises_clear_error(self):
        with self.assertRaises((ValueError, FileNotFoundError)) as ctx:
            Parser("")
        self.assertTrue(str(ctx.exception))

    def test_missing_file_raises_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            Parser("/nonexistent/campaign/file")

    def test_empty_campaign_file_parses_to_empty_sections(self):
        path = write_campaign("")
        try:
            characters, campaign, atmosphere, credits = Parser(path).parse_file()
            self.assertEqual(len(characters), 0)
            self.assertEqual(campaign, [])
            self.assertEqual(atmosphere, [])
            self.assertEqual(credits, [])
        finally:
            os.remove(path)

    def test_missing_stat_field_is_skipped_and_recovered(self):
        path = write_campaign(
            "#Characters\n"
            "Good: 100 50 10\n"
            "Broken: 100 50\n"
            "AlsoGood: 80 40 5\n"
            "#Campaign\n"
            "hello\n"
        )
        try:
            parser = Parser(path)
            characters, campaign, _, _ = parser.parse_file()
            self.assertEqual(len(characters), 2)
            self.assertIsNotNone(characters.get("Good"))
            self.assertIsNotNone(characters.get("AlsoGood"))
            self.assertTrue(len(parser.errors) >= 1)
            self.assertEqual(campaign, ["hello\n"])
        finally:
            os.remove(path)

    def test_blank_and_malformed_character_lines_are_skipped(self):
        path = write_campaign(
            "#Characters\n"
            "\n"
            "NoSeparatorHere\n"
            "Hero: not_a_number 50 10\n"
            "Valid: 10 10 10\n"
            "#Campaign\n"
        )
        try:
            parser = Parser(path)
            characters, _, _, _ = parser.parse_file()
            self.assertEqual(len(characters), 1)
            self.assertIsNotNone(characters.get("Valid"))
            self.assertEqual(len(parser.errors), 2)
        finally:
            os.remove(path)

    def test_character_array_bounds(self):
        arr = CharacterArray()
        arr.addCharacter(Character("Solo", 1, 1, 1))
        with self.assertRaises(IndexError):
            arr.at(5)
        with self.assertRaises(IndexError):
            arr.at(-1)
        self.assertIs(arr.at(0), arr.arr[0])
        self.assertIsNone(arr.get("Nobody"))
        with self.assertRaises(KeyError):
            arr.remove("Nobody")


class TestBattleSettlementInvariants(unittest.TestCase):
    def setUp(self):
        random.seed(1234)

    def quiet(self):
        return contextlib.ExitStack()

    def test_both_fighters_dead_is_a_draw(self):
        dead_a = Character("A", 10, 10, 10)
        dead_b = Character("B", 10, 10, 10)
        dead_a.health = 0
        dead_b.health = 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = Battle.getAttack(dead_a, dead_b)
        self.assertEqual(result, "Draw")
        self.assertNotIn("is victorious!", out.getvalue())

    def test_dead_attacker_cannot_act(self):
        dead = Character("Dead", 10, 10, 10)
        dead.health = 0
        alive = Character("Alive", 10, 10, 10)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = Battle.getAttack(dead, alive)
        self.assertEqual(result, "End")
        self.assertEqual(alive.health, 10)
        self.assertIn("Alive is victorious!", out.getvalue())

    def test_lethal_attack_declares_living_winner(self):
        attacker = Character("Strong", 10, 100, 0)
        defender = Character("Weak", 1, 0, 0)
        with contextlib.redirect_stdout(io.StringIO()):
            result = Battle.getAttack(attacker, defender)
        self.assertEqual(result, "End")
        self.assertLessEqual(defender.health, 0)
        self.assertGreater(attacker.health, 0)

    def test_full_battle_invariants(self):
        for seed in range(10):
            random.seed(seed)
            first = Character("First", 60, 40, 10)
            second = Character("Second", 60, 40, 10)
            with mock.patch("builtins.input", return_value=""), \
                    mock.patch("os.system"), \
                    contextlib.redirect_stdout(io.StringIO()):
                result = Battle().battle(first, second)
            self.assertIn(result, ("End", "Draw"))
            self.assertTrue(first.health <= 0 or second.health <= 0)
            if result == "End":
                self.assertFalse(first.health <= 0 and second.health <= 0)
            else:
                self.assertLessEqual(first.health, 0)
                self.assertLessEqual(second.health, 0)

    def test_skirmish_with_two_corpses_ends_immediately(self):
        dead_a = Character("A", 10, 10, 10)
        dead_b = Character("B", 10, 10, 10)
        dead_a.health = 0
        dead_b.health = 0
        with mock.patch("builtins.input") as input_mock, \
                mock.patch("os.system"), \
                contextlib.redirect_stdout(io.StringIO()):
            result = Battle().skirmish(dead_a, dead_b)
        self.assertEqual(result, "Draw")
        input_mock.assert_not_called()


class TestRegionStateIsolation(unittest.TestCase):
    def setUp(self):
        self.path = write_campaign(CAMPAIGN_TWO_FIGHTERS)
        self.addCleanup(os.remove, self.path)

    def make_region(self):
        with mock.patch("os.system"):
            return Region(self.path)

    def test_regions_do_not_share_character_state(self):
        region_a = self.make_region()
        region_b = self.make_region()
        self.assertIsNot(region_a.characters, region_b.characters)
        alpha_a = region_a.characters.get("Alpha")
        alpha_a.health = 3
        self.assertEqual(region_b.characters.get("Alpha").health, 100)

    def test_character_array_default_argument_is_not_shared(self):
        first = CharacterArray()
        second = CharacterArray()
        first.addCharacter()
        second.addCharacter()
        self.assertIsNot(first.arr[0], second.arr[0])
        first.arr[0].health = -50
        self.assertEqual(second.arr[0].health, 0)

    def test_dead_or_unknown_fighters_cannot_act(self):
        region = self.make_region()
        alpha = region.characters.get("Alpha")
        beta = region.characters.get("Beta")
        alpha.health = 0
        with mock.patch("builtins.input", return_value=""), \
                mock.patch("os.system"), \
                contextlib.redirect_stdout(io.StringIO()):
            result = region.doFunction("battle", "battle => Alpha, Beta")
        self.assertIsNone(result)
        self.assertEqual(beta.health, 100)
        with mock.patch("builtins.input", return_value=""), \
                mock.patch("os.system"), \
                contextlib.redirect_stdout(io.StringIO()):
            result = region.doFunction("battle", "battle => Alpha, Ghost")
        self.assertIsNone(result)

    def test_empty_region_game_loop_runs_to_completion(self):
        empty = write_campaign("")
        self.addCleanup(os.remove, empty)
        region = self.make_region()
        region.region_file = Parser(empty)
        region.characters, region.campaign, region.atmosphere, region.credits = \
            region.region_file.parse_file()
        with mock.patch("builtins.input", return_value=""), mock.patch("os.system"):
            self.assertIsNone(region.game_loop())


class TestFormatText(unittest.TestCase):
    def test_empty_segment(self):
        self.assertEqual(format_text(""), "")

    def test_basic_codes_still_work(self):
        self.assertEqual(format_text("[red]x[reset]"), "\u001b[31mx\u001b[0m")

    def test_long_segment_with_mixed_256_tags(self):
        line = "[__background256_100_]x[_text256_54_]y"
        formatted = format_text(line)
        self.assertIn("\u001b[48;5;100m", formatted)
        self.assertIn("\u001b[38;5;54m", formatted)
        self.assertNotIn("[_text256_", formatted)

    def test_very_long_segment_all_tags_replaced(self):
        line = " ".join("[_text256_{}_]".format(i % 256) for i in range(200))
        formatted = format_text(line)
        self.assertNotIn("[_text256_", formatted)
        self.assertEqual(formatted.count("\u001b[38;5;"), 200)

    def test_malformed_and_empty_tags_do_not_crash(self):
        for text in ("[_text256_]x", "[_text256_abc_]x", "unclosed [_text256_12",
                     "[__background256_]y", "[__background256_zz_]y"):
            self.assertEqual(format_text(text), text)

    def test_valid_tags_around_malformed_tag_still_format(self):
        formatted = format_text("[_text256_1_]a[_text256_]b[_text256_2_]c")
        self.assertIn("\u001b[38;5;1m", formatted)
        self.assertIn("\u001b[38;5;2m", formatted)


class TestExampleCampaignsRunToCompletion(unittest.TestCase):
    def run_example(self, script, stdin_text):
        return subprocess.run(
            [sys.executable, script],
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=REPO_DIR,
            timeout=180,
        )

    def test_fifth_season_example_completes(self):
        proc = self.run_example("The Fifth Season Example.py", "\n" * 200000)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertIn("Credits:", proc.stdout)

    def test_ascefelia_example_completes(self):
        stdin_text = ("\n" * 10 + "1\n") * 20000
        proc = self.run_example("Ascefelia Example.py", stdin_text)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertIn("Game Over", proc.stdout)


if __name__ == "__main__":
    unittest.main()
