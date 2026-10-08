# Renderizador para IA conversacional

El repositorio mantiene dos capas de presentación sobre el mismo motor termodinámico determinista:

- **Terminal**: texto compacto + esquema ASCII/Unicode.
- **IA normal / chat**: Markdown + LaTeX + tablas + gráficos SVG representativos.

Ninguno de los renderizadores calcula propiedades por su cuenta. Los dos reciben un `RankineResult` generado por el solver.

## Flujo de salida para chat

1. Datos del problema.
2. Tabla inicial con solo los datos del enunciado.
3. Datos obtenidos directamente de las tablas termodinámicas.
4. Resolución breve estado por estado.
5. Si existe una interpolación, se muestra inmediatamente dentro del estado correspondiente:
   - valores vecinos;
   - tabla local de interpolación;
   - gráfico guía SVG;
   - fórmula general;
   - sustitución numérica;
   - resultado interpolado.
6. Tabla final de estados.
7. Balances de energía y rendimiento térmico.

## Regla del gráfico de interpolación

El gráfico se diseña como **guía visual**, no como gráfico metrológico. Debe respetar el orden de los puntos, pero no necesita reproducir distancias ni pendientes a escala. Cada figura lleva una advertencia explícita de este criterio.

## Uso

```bash
python thermo.py rankine-chat \
  --boiler-bar 70 \
  --condenser-bar 0.1 \
  --turbine-inlet-c 478 \
  --output outputs/chat_demo
```

Genera:

```text
outputs/chat_demo/
├── chat_solution.md
├── chat_solution.json
└── figures/
    ├── interpolacion_estado_3_01.svg
    └── interpolacion_estado_3_02.svg
```

`chat_solution.md` está pensado para copiarse o integrarse directamente en una interfaz de IA que renderice Markdown y LaTeX.
