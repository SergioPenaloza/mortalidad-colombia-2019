"""Plotly figures: presentation only, with calculations in analytics.py."""

from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go

from src.analytics import age_counts, count_by, format_count, monthly_counts, municipality_ranking
from src.settings import AGE_GROUPS, MONTHS, SEX_LABELS

INK = "#183447"
MUTED = "#6f8190"
TEAL = "#168b86"
NAVY = "#244b69"
GRID = "#edf1f4"
SEX_COLORS = {1: "#244b69", 2: "#36a89c", 3: "#b4bdc6"}
PIE_COLORS = ["#244b69", "#168b86", "#53aaa0", "#99c7b9", "#d7bf82", "#b68c57", "#8b9eb5", "#bdcbd7", "#788b72", "#d4dace"]


def plotly_geometry(geography: dict) -> dict:
    """D3 spherical polygons require clockwise exterior rings, unlike RFC 7946."""
    result = deepcopy(geography)
    for feature in result["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            for index, ring in enumerate(polygon):
                signed_area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))
                if (index == 0 and signed_area > 0) or (index > 0 and signed_area < 0):
                    ring.reverse()
    return result


def base(figure: go.Figure, height: int = 350) -> go.Figure:
    figure.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=16, r=24, t=30, b=40),
        font=dict(family="Segoe UI, Arial, sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor=INK, font_color="white", bordercolor=INK, font_size=13),
        separators=",.", dragmode=False,
        legend=dict(orientation="h", x=0, y=1.08, font_size=12),
    )
    figure.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True, title_font_size=11)
    figure.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True, title_font_size=11)
    return figure


def empty_figure(message: str = "No hay registros para esta selección.", height: int = 350) -> go.Figure:
    figure = base(go.Figure(), height)
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color=MUTED))
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure


def department_map(frame: pd.DataFrame, geography: dict) -> go.Figure:
    if frame.empty:
        return empty_figure(height=450)
    values = count_by(frame, ["department", "department_name"])
    geography = plotly_geometry(geography)
    figure = go.Figure(go.Choropleth(
        geojson=geography, featureidkey="id", locations=values.department.astype(str).tolist(),
        z=values.deaths.tolist(), zmin=0, zmax=int(values.deaths.max()), zauto=False,
        customdata=[[str(r.department_name), format_count(r.deaths)] for r in values.itertuples()],
        colorscale=[[0, "#dceee7"], [0.25, "#9accc0"], [0.55, "#32988c"], [1, "#164c52"]],
        marker_line_color="#ffffff", marker_line_width=0.8,
        colorbar=dict(title=dict(text="Defunciones", side="top"), thickness=9, len=0.65, x=0.96, tickfont_size=10, tickformat=",.0f", nticks=5, dtick=1 if values.deaths.max() <= 5 else None),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} defunciones<extra></extra>",
    ))
    # A pale base preserves context for departments outside the active selection.
    figure.add_trace(go.Choropleth(
        geojson=geography, featureidkey="id",
        locations=[f["id"] for f in geography["features"] if f["id"] not in set(values.department)],
        z=[0] * (len(geography["features"]) - len(values)),
        colorscale=[[0, "#edf1f2"], [1, "#edf1f2"]], showscale=False,
        marker_line_color="white", marker_line_width=0.8, hoverinfo="skip",
    ))
    islands = values.loc[values.department.eq("88")]
    if not islands.empty:
        # At national scale the island polygons are smaller than a screen pixel.
        figure.add_trace(go.Scattergeo(
            lon=[-81.70], lat=[12.58], mode="markers+text", showlegend=False,
            text=["San Andrés y<br>Providencia"], textposition="bottom right",
            textfont=dict(size=9, color=MUTED), marker=dict(size=5, color=NAVY),
            customdata=[format_count(islands.deaths.sum())],
            hovertemplate="<b>San Andrés y Providencia</b><br>%{customdata} defunciones<extra></extra>",
        ))
    base(figure, 450)
    figure.update_geos(
        visible=False, projection_type="mercator", resolution=110,
        lonaxis_range=[-82.2, -66.4], lataxis_range=[-4.5, 13.8],
        bgcolor="rgba(0,0,0,0)", showframe=False,
    )
    figure.update_layout(margin=dict(l=0, r=12, t=0, b=0), uirevision="colombia-2019")
    return figure


def monthly_line(frame: pd.DataFrame, months: tuple[int, ...] = ()) -> go.Figure:
    if frame.empty:
        return empty_figure(height=290)
    values = monthly_counts(frame, months)
    figure = go.Figure(go.Scatter(
        x=values.index.tolist(), y=values.tolist(), mode="lines+markers",
        line=dict(color=TEAL, width=3, shape="linear"),
        marker=dict(size=7, color=TEAL, line=dict(color="white", width=2)),
        fill="tozeroy", fillcolor="rgba(22,139,134,0.07)",
        customdata=[[MONTHS[m - 1], format_count(n)] for m, n in values.items()],
        hovertemplate="<b>%{customdata[0]} de 2019</b><br>%{customdata[1]} defunciones<extra></extra>",
    ))
    base(figure, 290)
    figure.update_xaxes(tickmode="array", tickvals=values.index.tolist(), ticktext=[MONTHS[m - 1][:3] for m in values.index], showgrid=False)
    figure.update_yaxes(rangemode="tozero", title_text="Defunciones", nticks=5)
    figure.update_layout(margin=dict(l=10, r=12, t=20, b=35))
    return figure


def violent_cities(frame: pd.DataFrame) -> go.Figure:
    ranking = municipality_ranking(frame)
    if ranking.empty:
        return empty_figure("No se registran casos X95 en municipios de esta selección.", 330)
    ranking = ranking.iloc[::-1]
    labels = [f"{r.municipality_name}<br><span style='font-size:10px;color:{MUTED}'>{r.department_name}</span>" for r in ranking.itertuples()]
    figure = go.Figure(go.Bar(
        x=ranking.deaths.tolist(), y=labels, orientation="h",
        marker_color=["#8bbfb6"] * (len(ranking) - 1) + [TEAL],
        text=[format_count(v) for v in ranking.deaths], textposition="outside", cliponaxis=False,
        customdata=ranking.municipality.astype(str).tolist(),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} defunciones X95<br>Código DANE: %{customdata}<extra></extra>",
    ))
    base(figure, 330)
    figure.update_xaxes(title_text="Defunciones por causas X95", range=[0, int(ranking.deaths.max()) * 1.24])
    figure.update_yaxes(showgrid=False, tickfont_size=12)
    figure.update_layout(bargap=0.46, margin=dict(l=10, r=15, t=15, b=35))
    return figure


def lowest_cities(frame: pd.DataFrame) -> go.Figure:
    ranking = municipality_ranking(frame, lowest=True)
    if ranking.empty:
        return empty_figure("No hay municipios con registros en esta selección.", 300)
    figure = go.Figure(go.Pie(
        labels=[f"{r.municipality_name} · {r.department_name}" for r in ranking.itertuples()],
        values=ranking.deaths.tolist(), hole=0.73, sort=False, direction="clockwise", rotation=20,
        marker=dict(colors=PIE_COLORS, line=dict(color="white", width=3)),
        textinfo="none", showlegend=False,
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} defunciones<br>%{percent} del grupo seleccionado<extra></extra>",
    ))
    base(figure, 285)
    figure.add_annotation(text=f"<b>{format_count(ranking.deaths.sum())}</b>", x=0.5, y=0.54, showarrow=False, font=dict(size=34, color=INK))
    figure.add_annotation(text=f"casos en {len(ranking)} municipios", x=0.5, y=0.40, showarrow=False, font=dict(size=11, color=MUTED))
    figure.update_layout(margin=dict(l=15, r=15, t=15, b=15))
    return figure


def sex_by_department(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure(height=710)
    values = count_by(frame, ["department_name", "sex"])
    order = frame.groupby("department_name", observed=True).deaths.sum().sort_values().index.tolist()
    figure = go.Figure()
    for code, name in SEX_LABELS.items():
        counts = values.loc[values.sex.eq(code)].set_index("department_name").deaths.reindex(order, fill_value=0)
        figure.add_trace(go.Bar(
            name=name, x=counts.tolist(), y=order, orientation="h", marker_color=SEX_COLORS[code],
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:,.0f}}<extra></extra>",
        ))
    base(figure, max(300, 90 + 19 * len(order)))
    figure.update_layout(barmode="stack", bargap=0.3, legend=dict(y=1.06), margin=dict(l=5, r=20, t=45, b=35))
    figure.update_xaxes(title_text="Defunciones")
    figure.update_yaxes(showgrid=False, categoryorder="array", categoryarray=order, tickfont_size=11)
    return figure


def age_histogram(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure(height=380)
    counts = age_counts(frame)
    figure = go.Figure(go.Bar(
        x=[group[1] for group in AGE_GROUPS], y=counts.tolist(),
        marker_color=[TEAL] * 8 + [NAVY, "#7294a8", "#c3cbd1"],
        customdata=[[group[0], format_count(counts.iloc[i])] for i, group in enumerate(AGE_GROUPS)],
        hovertemplate="<b>%{customdata[0]}</b><br>%{x}<br>%{customdata[1]} defunciones<extra></extra>",
    ))
    base(figure, 380)
    figure.update_xaxes(tickangle=-40, showgrid=False, title_text="Grupos de edad de la actividad")
    figure.update_yaxes(title_text="Defunciones", rangemode="tozero")
    figure.update_layout(bargap=0.18, margin=dict(l=10, r=10, t=20, b=90))
    return figure
