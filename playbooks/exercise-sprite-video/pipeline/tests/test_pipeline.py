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
VALID_WHEN = {"all", "jump", "prone", "supine", "multirow", "touch", "front", "inline"}


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


class Orientation(unittest.TestCase):
    """The 'start flat' rule must match how the exercise lies (review finding on PR #30)."""

    def prompt(self, key):
        e = S.find_exercise(EXS, key)
        return gen.sprite_prompt(e, S.load_character("boy"), RULES, STAGE)[0]

    def test_supine_exercises_are_not_told_to_lie_face_down(self):
        for k in ("sit-up-toe-touch-c4", "sit-up-twist-c5", "pike-sit-up-c6"):
            p = self.prompt(k)
            self.assertNotIn("face down: belly", p, k)
            self.assertIn("flat on the back", p, k)

    def test_prone_exercises_keep_the_face_down_rule(self):
        for k in ("back-extension-c2", "back-extension-press-c6"):
            self.assertIn("flat face down", self.prompt(k), k)


class Segmentation(unittest.TestCase):
    def test_attached_piece_grows_the_figure_box(self):
        import numpy as np
        a = np.zeros((200, 300, 3), np.uint8); a[:] = (255, 0, 255)
        a[50:150, 100:160] = (0, 0, 0)            # the figure body
        a[100:112, 175:187] = (0, 0, 0)           # a detached piece 15 px to the right of the body
        rows, lab = S.segment(a, np.array([255., 0., 255.]), min_area_frac=0.05, attach_dist=30)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 1)
        x, y, w, h = rows[0][0]["bbox"]
        self.assertGreaterEqual(x + w, 187, "box must include the attached piece")


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
