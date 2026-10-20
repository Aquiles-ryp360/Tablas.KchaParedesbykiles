"""Consulta de las tablas R600a aportadas en tablas.pdf (sin extrapolación)."""
from __future__ import annotations

import bisect
import csv
import json
import math
from pathlib import Path


class R600aTables:
    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory) if directory else Path(__file__).resolve().parents[2] / 'data' / 'r600a'
        self.saturated = self._read('saturated.csv')
        self.vapor = {name: self._read(name + '.csv') for name in ('volume', 'enthalpy', 'entropy')}

    def _read(self, name):
        with (self.directory / name).open(encoding='utf-8', newline='') as f:
            return [{k: float(v) if v else None for k, v in row.items()} for row in csv.DictReader(f)]

    @staticmethod
    def _bracket(values, value):
        if not math.isfinite(value) or value < values[0] or value > values[-1]:
            raise ValueError(f'Valor fuera de la tabla: {value}; límites {values[0]}..{values[-1]}')
        i = bisect.bisect_left(values, value)
        return (i, i) if values[i] == value else (i - 1, i)

    @staticmethod
    def _lerp(x, a, b, ya, yb):
        if ya is None or yb is None:
            raise ValueError('La consulta requiere una celda pendiente de verificar en el escaneo')
        return ya if a == b else ya + (x - a) / (b - a) * (yb - ya)

    def saturation(self, pressure_bar: float):
        p = float(pressure_bar)
        i, j = self._bracket([r['P_bar'] for r in self.saturated], p)
        a, b = self.saturated[i], self.saturated[j]
        result = {k: self._lerp(p, a['P_bar'], b['P_bar'], a[k], b[k]) for k in a}
        result['v_f_m3kg'] = result['v_f_dm3kg'] / 1000
        result['source_rows'] = [i + 1, j + 1]
        return result

    def pt(self, pressure_bar: float, temperature_c: float):
        p, t = float(pressure_bar), float(temperature_c)
        if not math.isfinite(t):
            raise ValueError('Temperatura no finita')
        i, j = self._bracket([r['P_bar'] for r in self.saturated], p)
        result = {'P_bar': p, 'T_C': t, 'interpolations': []}
        for name, key in [('volume', 'v_dm3kg'), ('enthalpy', 'h_kJkg'), ('entropy', 's_kJkgK')]:
            endpoints = []
            for r in dict.fromkeys((i, j)):
                row = self.vapor[name][r]
                delta = t - row['T_sat_C']
                lo, hi = self._bracket(list(range(0, 101, 5)), delta)
                dl, dh = lo * 5, hi * 5
                a, b = row[f'dT_{dl}_C'], row[f'dT_{dh}_C']
                value = self._lerp(delta, dl, dh, a, b)
                endpoints.append(value)
                result['interpolations'].append(dict(property=key, source_page={'volume': 2, 'enthalpy': 3, 'entropy': 4}[name], source_row=r+1, P_bar=row['P_bar'], T_sat_C=row['T_sat_C'], superheat_C=delta, bounds_C=[dl, dh], bounds_values=[a,b], value=value))
            pa, pb = self.saturated[i]['P_bar'], self.saturated[j]['P_bar']
            result[key] = self._lerp(p, pa, pb, endpoints[0], endpoints[-1])
        result['v_m3kg'] = result['v_dm3kg'] / 1000
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pressure-bar', type=float, required=True)
    parser.add_argument('--temperature-c', type=float)
    args = parser.parse_args()
    tables = R600aTables()
    result = tables.saturation(args.pressure_bar) if args.temperature_c is None else tables.pt(args.pressure_bar, args.temperature_c)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
