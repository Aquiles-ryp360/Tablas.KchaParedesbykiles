from __future__ import annotations

"""Renderizado orientado a asistentes de IA / chat.

Este módulo NO calcula propiedades termodinámicas. Solo transforma un
``RankineResult`` ya resuelto por el motor determinista en una presentación
Markdown + LaTeX, manteniendo trazabilidad de tablas, interpolaciones y balances.
"""

import json
from pathlib import Path

from .interpolation import render_svg
from .models import InterpolationEvent, RankineResult
from .state_table import markdown_state_table


def _fmt(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}g}"


def _event_formula(event: InterpolationEvent) -> tuple[str, str]:
    """Devuelve fórmula general y sustitución en LaTeX."""
    prop = event.property_name
    x = event.x_name
    general = (
        rf"{prop}={prop}_1+\frac{{{x}-{x}_1}}{{{x}_2-{x}_1}}"
        rf"\left({prop}_2-{prop}_1\right)"
    )
    substitution = (
        rf"{prop}={_fmt(event.y1)}+"
        rf"\frac{{{_fmt(event.x)}-{_fmt(event.x1)}}}"
        rf"{{{_fmt(event.x2)}-{_fmt(event.x1)}}}"
        rf"\left({_fmt(event.y2)}-{_fmt(event.y1)}\right)"
    )
    return general, substitution


def _event_markdown(
    event: InterpolationEvent,
    *,
    figure_relpath: str,
) -> list[str]:
    xu = f" {event.x_unit}" if event.x_unit else ""
    yu = f" {event.y_unit}" if event.y_unit else ""
    general, substitution = _event_formula(event)

    lines = [
        f"#### {event.method.capitalize()} de ${event.property_name}$",
        "",
        f"El valor exacto de **{event.x_name} = {_fmt(event.x)}{xu}** no está tabulado. "
        "Se toman los dos valores vecinos inmediatos.",
        "",
        f"| Punto | {event.x_name} ({event.x_unit or '—'}) | {event.property_name} ({event.y_unit or '—'}) |",
        "|---|---:|---:|",
        f"| Inferior | {_fmt(event.x1)} | {_fmt(event.y1)} |",
        f"| Buscado | **{_fmt(event.x)}** | **?** |",
        f"| Superior | {_fmt(event.x2)} | {_fmt(event.y2)} |",
        "",
    ]
    if event.note:
        lines.extend([f"> Condición de referencia: **{event.note}**", ""])

    lines.extend(
        [
            "**Gráfico guía de interpolación**",
            "",
            f"![Gráfico guía de interpolación]({figure_relpath})",
            "",
            "> **Nota:** el gráfico es representativo y deliberadamente no está necesariamente a escala. "
            "Su función es mostrar con claridad la posición del punto buscado entre los valores tabulados.",
            "",
            "**Fórmula**",
            "",
            rf"\[{general}\]",
            "",
            "**Sustitución**",
            "",
            rf"\[{substitution}\]",
            "",
            "**Resultado interpolado**",
            "",
            rf"\[\boxed{{{event.property_name}={_fmt(event.result)}\ {yu.strip()}}}\]",
            "",
        ]
    )
    return lines


def rankine_chat_markdown(
    result: RankineResult,
    *,
    figure_dir: Path | None = None,
    figure_prefix: str = "figures",
) -> str:
    """Genera una respuesta Markdown/LaTeX pensada para una IA conversacional.

    Si ``figure_dir`` se proporciona, se generan SVG de todas las interpolaciones.
    Los SVG se insertan inmediatamente debajo del estado donde se producen.
    """

    p_high = result.inputs["boiler_pressure_bar"]
    p_low = result.inputs["condenser_pressure_bar"]
    t3 = result.inputs["turbine_inlet_temperature_C"]

    parts: list[str] = [
        "# Resolución paso a paso — ciclo Rankine ideal",
        "",
        "La resolución se organiza primero con los datos del enunciado, después se consultan las tablas "
        "termodinámicas y finalmente se completa cada estado. Si un valor no aparece exactamente en la "
        "base, la interpolación se muestra con su gráfico guía, fórmula, sustitución y resultado.",
        "",
        "## 1. Datos del problema",
        "",
        rf"\[P_{{caldera}}={_fmt(p_high)}\ \text{{bar}}\]",
        rf"\[P_{{condensador}}={_fmt(p_low)}\ \text{{bar}}\]",
        rf"\[T_3={_fmt(t3)}^\circ C\]",
        "",
        "## 2. Tabla inicial de estados",
        "",
        "En esta primera tabla solo se colocan los datos conocidos directamente del problema.",
        "",
        markdown_state_table(result.initial_states),
        "",
        "## 3. Datos obtenidos directamente de las tablas termodinámicas",
        "",
        markdown_state_table(result.table_states),
        "",
        "## 4. Resolución estado por estado",
        "",
    ]

    figure_counter = 0
    for state_number, explanation in enumerate(result.state_explanations, start=1):
        parts.extend(
            [
                f"### Estado {state_number}",
                "",
                explanation,
                "",
            ]
        )
        events = result.events_by_state.get(state_number, [])
        for event in events:
            figure_counter += 1
            figure_name = f"interpolacion_estado_{state_number}_{figure_counter:02d}.svg"
            if figure_dir is not None:
                figure_dir.mkdir(parents=True, exist_ok=True)
                render_svg(
                    event,
                    figure_dir / figure_name,
                    title=f"Guía de {event.method}: {event.property_name}",
                )
            rel = f"{figure_prefix}/{figure_name}"
            parts.extend(_event_markdown(event, figure_relpath=rel))

        # Una foto compacta de cómo queda el estado tras resolverlo.
        st = result.final_states[state_number - 1]
        parts.extend(
            [
                "**Estado obtenido**",
                "",
                "| P (bar) | T (°C) | x | h (kJ/kg) | s (kJ/kg·K) | Fase |",
                "|---:|---:|---:|---:|---:|---|",
                f"| {_fmt(st.P_bar)} | {_fmt(st.T_C)} | {_fmt(st.x)} | {_fmt(st.h_kJkg)} | {_fmt(st.s_kJkgK)} | {st.phase or '—'} |",
                "",
            ]
        )

    parts.extend(
        [
            "## 5. Tabla final de estados",
            "",
            markdown_state_table(result.final_states),
            "",
            "## 6. Balances y resultados del ciclo",
            "",
            "### Trabajo de la turbina",
            "",
            rf"\[W_t=h_3-h_4={_fmt(result.final_states[2].h_kJkg)}-{_fmt(result.final_states[3].h_kJkg)}\]",
            rf"\[\boxed{{W_t={_fmt(result.turbine_work_kJkg)}\ \text{{kJ/kg}}}}\]",
            "",
            "### Trabajo de la bomba",
            "",
            rf"\[W_b=h_2-h_1\]",
            rf"\[\boxed{{W_b={_fmt(result.pump_work_kJkg)}\ \text{{kJ/kg}}}}\]",
            "",
            "### Calor suministrado",
            "",
            rf"\[Q_{{in}}=h_3-h_2\]",
            rf"\[\boxed{{Q_{{in}}={_fmt(result.heat_in_kJkg)}\ \text{{kJ/kg}}}}\]",
            "",
            "### Calor rechazado",
            "",
            rf"\[Q_{{out}}=h_4-h_1\]",
            rf"\[\boxed{{Q_{{out}}={_fmt(result.heat_out_kJkg)}\ \text{{kJ/kg}}}}\]",
            "",
            "### Trabajo neto",
            "",
            rf"\[W_{{neto}}=W_t-W_b\]",
            rf"\[\boxed{{W_{{neto}}={_fmt(result.net_work_kJkg)}\ \text{{kJ/kg}}}}\]",
            "",
            "### Rendimiento térmico",
            "",
            rf"\[\eta_{{th}}=\frac{{W_{{neto}}}}{{Q_{{in}}}}\]",
            rf"\[\boxed{{\eta_{{th}}={_fmt(result.thermal_efficiency * 100)}\%}}\]",
            "",
            "---",
            "",
            "**Trazabilidad:** las propiedades usadas proceden de la base termodinámica, de una "
            "interpolación registrada o de una ecuación explícita del ciclo. El renderizador de IA no "
            "recalcula ni inventa propiedades; únicamente presenta los resultados del motor determinista.",
        ]
    )

    return "\n".join(parts)


def write_rankine_chat_report(result: RankineResult, output_dir: str | Path) -> Path:
    """Guarda el paquete de salida para una IA conversacional."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures = output / "figures"
    figures.mkdir(exist_ok=True)

    markdown = rankine_chat_markdown(
        result,
        figure_dir=figures,
        figure_prefix="figures",
    )
    path = output / "chat_solution.md"
    path.write_text(markdown, encoding="utf-8")
    (output / "chat_solution.json").write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
