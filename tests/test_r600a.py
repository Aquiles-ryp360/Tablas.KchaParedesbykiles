from __future__ import annotations
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from thermo_solver.r600a import R600aTables


class R600aTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = R600aTables()

    def test_table_shapes_and_pressures(self):
        self.assertEqual(len(self.t.saturated), 48)
        pressure = [r['P_bar'] for r in self.t.saturated]
        self.assertTrue(all(a < b for a, b in zip(pressure, pressure[1:])))
        for rows in self.t.vapor.values():
            self.assertEqual(len(rows), 48)
            self.assertEqual([r['P_bar'] for r in rows], pressure)
            self.assertTrue(all(len(r) == 23 for r in rows))
            for row in rows:
                values = [row[f'dT_{i}_C'] for i in range(0, 101, 5)]
                self.assertTrue(all(math.isfinite(v) for v in values))
                self.assertTrue(all(a < b for a, b in zip(values, values[1:])))

    def test_saturated_references_and_printed_rounding(self):
        r = self.t.saturation(1.570)
        self.assertEqual(r['h_f_kJkg'], 200)
        self.assertEqual(r['s_f_kJkgK'], 1)
        self.assertAlmostEqual(r['v_f_m3kg'], .001722)
        for i, r in enumerate(self.t.saturated):
            self.assertAlmostEqual(r['h_g_kJkg']-r['h_f_kJkg'], r['h_fg_kJkg'], delta=.003)
            self.assertEqual(self.t.vapor['enthalpy'][i]['dT_0_C'], r['h_g_kJkg'])
            self.assertEqual(self.t.vapor['entropy'][i]['dT_0_C'], r['s_g_kJkgK'])
            self.assertAlmostEqual(self.t.vapor['volume'][i]['dT_0_C']/1000, r['v_g_m3kg'], delta=.00051)

    def test_pt_uses_superheat_of_each_pressure_row(self):
        actual = self.t.pt(32.5, 145)
        expected = 761.181 + (32.5-30.880)/(33.578-30.880)*(749.729-761.181)
        self.assertAlmostEqual(actual['h_kJkg'], expected, places=9)
        h_events = [e for e in actual['interpolations'] if e['property']=='h_kJkg']
        self.assertEqual([e['superheat_C'] for e in h_events], [20, 15])
        self.assertAlmostEqual(actual['v_m3kg'], actual['v_dm3kg']/1000)

    def test_second_pt_and_saturated_interpolation(self):
        fraction=(4-3.507)/(4.047-3.507)
        self.assertAlmostEqual(self.t.pt(4,80)['h_kJkg'],691.396+fraction*(689.934-691.396))
        self.assertAlmostEqual(self.t.saturation(4)['h_f_kJkg'],258.980+fraction*(271.241-258.980))

    def test_exact_last_row_and_invalid_domain(self):
        self.assertEqual(self.t.pt(33.578,145)['h_kJkg'],749.729)
        for p,t in [(35,145),(.001,0),(32.5,120),(4,200),(float('nan'),80),(4,float('inf'))]:
            with self.assertRaises(ValueError):self.t.pt(p,t)


if __name__ == '__main__':
    unittest.main()
