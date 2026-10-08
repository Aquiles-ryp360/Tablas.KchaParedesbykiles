# Changelog

## 0.2.0 — 2026-10-07

- Se añade un renderizador dedicado para IA conversacional.
- La salida de chat usa Markdown, LaTeX, tablas y SVG representativos.
- Cada interpolación aparece dentro del estado correspondiente con valores vecinos, fórmula, sustitución y resultado.
- Se incorpora el comando `rankine-chat`.
- Se añaden pruebas automáticas del renderizado y generación de figuras.

## 0.1.0 — 2026-10-07

- Se conserva la base SQLite original y su auditoría.
- Se añade un motor de consultas de saturación y estados P-T/P-s.
- Se añade interpolación lineal y bilineal con trazabilidad.
- Se generan diagramas SVG representativos para cada interpolación.
- Se añade un solver de ciclo Rankine ideal simple de cuatro estados.
- Se generan reportes TXT, Markdown y JSON.
- Se añade CLI, pruebas automatizadas y CI para GitHub Actions.
