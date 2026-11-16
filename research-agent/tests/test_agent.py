"""Тесты CLI: python -m unittest discover -s tests -v"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args, cwd):
    return subprocess.run([sys.executable, "scripts/agent.py", *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


class AgentCLITest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for d in ("scripts", "templates", "config", "projects"):
            shutil.copytree(ROOT / d, self.tmp / d)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_demo_project_passes_strict_check(self):
        r = run("-p", "meditation-retention", "check", "--strict", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_new_project_and_gate(self):
        r = run("new", "test-case", "Почему падают продажи?", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.tmp / "projects/ACTIVE").read_text().strip(), "test-case")
        # пустой бриф не даёт закрыть этап
        r = run("advance", cwd=self.tmp)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("brief.md", r.stdout)

    def test_fact_without_source_and_missing_status_quo(self):
        run("new", "bad", "x", cwd=self.tmp)
        p = self.tmp / "projects/bad"
        (p / "picture.md").write_text("- [ФАКТ] (C1) Без источника\n- [ПРОБЕЛ] (C2) нет данных\n", encoding="utf-8")
        (p / "options.md").write_text("## Вариант 1: A\nТип: изменение\n### Сильные возражения\n- серьёзное\n", encoding="utf-8")
        r = run("check", "--strict", cwd=self.tmp)
        out = r.stdout
        self.assertIn("без ссылки на источник", out)
        self.assertIn("без «Причина:»", out)
        self.assertIn("статус-кво", out)
        self.assertIn("нужно не меньше 3", out)

    def test_pii_and_secret_detection(self):
        run("new", "pii", "x", cwd=self.tmp)
        (self.tmp / "projects/pii/materials/notes.md").write_text(
            "Респондент: ivan@example.com, +7 916 123-45-67\napi_key = abcdefghijklmnop1234\n", encoding="utf-8")
        r = run("check", cwd=self.tmp)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("e-mail", r.stdout)
        self.assertIn("телефон", r.stdout)
        self.assertIn("секрет", r.stdout)

    def test_source_add_is_idempotent(self):
        run("new", "src", "x", cwd=self.tmp)
        a = run("source", "add", "--title", "T", "--ref", "https://e.org", "--grade", "B", "--note", "n", cwd=self.tmp)
        b = run("source", "add", "--title", "T", "--ref", "https://e.org", "--grade", "B", "--note", "n", cwd=self.tmp)
        self.assertEqual(a.stdout.strip(), "S1")
        self.assertIn("повтор пропущен", b.stdout)

    def test_retention_and_revisit(self):
        csv = self.tmp / "projects/meditation-retention/materials/SYNTHETIC_events.csv"
        r = run("retention", str(csv), cwd=self.tmp)
        self.assertIn("| D7 |", r.stdout)
        r = run("-p", "meditation-retention", "revisit", "--source", "S6", cwd=self.tmp)
        self.assertIn("D1", r.stdout)


if __name__ == "__main__":
    unittest.main()
