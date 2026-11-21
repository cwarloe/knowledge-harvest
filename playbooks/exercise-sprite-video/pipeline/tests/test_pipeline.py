"""Checks that the pipeline itself still works. Run from the pipeline folder:  python -m unittest discover tests -v
These tests need no images from ChatGPT; they guard the config files and the generators."""
import os, re, sys, tempfile, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import sheetlib as S
import gen

BRIEFS = os.path.join(os.path.dirname(HERE), "briefs", "BATCH-A-sprites.md")
RULES = S.load_toml(os.path.join(HERE, "rules.toml"))["rule"]
STAGE = S.load_stage()
EXS = S.load_exercises()
VALID_WHEN = {"all", "jump", "lying", "multirow", "touch", "front", "inline"}


class Library(unittest.TestCase):
    def test_every_exercise_is_consistent(self):
        self.assertEqual(len(EXS), 18)
        for e in EXS:
            q = e["qc"]
            self.assertEqual(len(e["poses"]), q["per_row"], e["id"])
            for i in q.get("grounded", []):
                self.assertLess(i, q["per_row"], e["id"])
            for k in (q.get("airborne") or {}):
                self.assertLess(int(k), q["per_row"], e["id"])
            self.assertTrue(set(e.get("tags", [])) <= VALID_WHEN, e["id"])

    def test_rules_use_known_tags(self):
        for r in RULES:
            self.assertIn(r["when"], VALID_WHEN, r["id"])
            self.assertRegex(r["defect"], r"^D-\d\d$")

    def test_job_numbers_unique(self):
        jobs = [e["job"] for e in EXS]
        self.assertEqual(len(jobs), len(set(jobs)))


class CharacterSwap(unittest.TestCase):
    """A new character must need only its own .toml file: no leftover words from the boy, no unfilled tokens."""

    def render(self, name):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "b.md")
            gen.build_batch(name, "all", "fresh", out)
            with open(out, encoding="utf-8") as f:
                return f.read()

    def test_girl_has_no_boy_leakage(self):
        t = self.render("example-teen-girl")
        for pat in (r"\bboy\b", r"\b[Hh]e\b", r"\b[Hh]is\b", r"\bhim\b", r"tights", r"red shorts", r"cyan", r"spiky", r"12-year"):
            self.assertIsNone(re.search(pat, t), f"leaked: {pat}")
        self.assertIsNone(re.search(r"\{[A-Za-z]+\}", t), "unfilled token")
        self.assertIn("girl", t)

    def test_boy_has_no_unfilled_tokens(self):
        t = self.render("boy")
        self.assertIsNone(re.search(r"\{[A-Za-z]+\}", t))

    def test_fix_mode_covers_every_fix(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "f.md")
            n = gen.build_batch("boy", "all", "fix", out)
            fixes = S.load_toml(os.path.join(HERE, "fixes.toml"))["fix"]
            self.assertEqual(n, len(fixes))


@unittest.skipUnless(os.path.exists(BRIEFS), "original briefs not found")
class Regression(unittest.TestCase):
    """For the boy, the generator must still carry the content of the hand-written overnight prompts."""

    def test_first_draw_prompts_keep_the_original_content(self):
        with open(BRIEFS, encoding="utf-8") as f:
            txt = f.read()
        parts = re.split(r"(?m)^=== JOB-(\d\d) of \d+: (.*?) ===\n", txt)
        orig = {int(parts[i]): parts[i + 2].split("PROMPT:")[1] for i in range(1, len(parts), 3)}
        norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'")).strip().lower()
        ch = S.load_character("boy")
        for e in EXS:
            if e["job"] < 9 and e["job"] != 2:   # jobs 1, 3-8 were written as retakes with a different preamble
                continue
            g = norm(gen.sprite_prompt(e, ch, RULES, STAGE)[0])
            ps = []
            for line in orig[e["job"]].split("\n"):
                ps += [norm(x) for x in re.split(r"(?<=[.;:])\s+", line.strip()) if len(x) > 25]
            ps = [p for p in ps if not p.startswith("the ") or "poses" not in p]
            hit = sum(1 for p in ps if p in g) / len(ps)
            self.assertGreaterEqual(hit, 0.9, f"JOB-{e['job']:02d} only {hit:.0%} of the original content survives")


class Mats(unittest.TestCase):
    def test_code_drawn_mats_pass_qc(self):
        import mats, qc
        with tempfile.TemporaryDirectory() as d:
            names = mats.draw_all(d)
            self.assertEqual(len(names), 4)
            for n in names:
                _, fmt, colour = n.split("-")
                rep = qc.qc_mat(os.path.join(d, n + ".png"), fmt, colour, STAGE)
                self.assertEqual(rep.worst, qc.OK, f"{n}: {rep.rows}")


if __name__ == "__main__":
    unittest.main()
