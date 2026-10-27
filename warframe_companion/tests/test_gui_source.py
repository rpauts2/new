from pathlib import Path
import unittest


class GuiSourceTests(unittest.TestCase):
    def test_gui_module_compiles_without_opening_a_window(self):
        source = Path(__file__).resolve().parents[1] / "gui.py"
        compile(source.read_text(encoding="utf-8"), str(source), "exec")


if __name__ == "__main__":
    unittest.main()
