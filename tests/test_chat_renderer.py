from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from thermo_solver.chat_renderer import rankine_chat_markdown, write_rankine_chat_report
from thermo_solver.database import ThermoDatabase
from thermo_solver.rankine import solve_rankine_ideal


class ChatRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        db = ThermoDatabase(ROOT / "data" / "thermodynamic_tables.sqlite")
        # 478 °C obliga interpolación en el estado 3 para verificar el gráfico.
        self.result = solve_rankine_ideal(
            boiler_pressure_bar=70.0,
            condenser_pressure_bar=0.1,
            turbine_inlet_temperature_C=478.0,
            database=db,
        )

    def test_chat_markdown_has_expected_sections(self) -> None:
        md = rankine_chat_markdown(self.result)
        self.assertIn("Tabla inicial de estados", md)
        self.assertIn("Resolución estado por estado", md)
        self.assertIn("Interpolación lineal", md)
        self.assertIn("Gráfico guía", md)
        self.assertIn("Rendimiento térmico", md)
        self.assertIn("Trazabilidad", md)

    def test_chat_report_creates_svg_for_interpolation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = write_rankine_chat_report(self.result, td)
            self.assertTrue(path.exists())
            figures = list((Path(td) / "figures").glob("*.svg"))
            self.assertGreaterEqual(len(figures), 1)
            text = path.read_text(encoding="utf-8")
            self.assertIn("no está necesariamente a escala", text)


if __name__ == "__main__":
    unittest.main()
