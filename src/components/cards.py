"""Small reusable Dash components, independent of the data layer."""

from dash import dcc, html


GRAPH_CONFIG = {
    "displaylogo": False, "responsive": True, "scrollZoom": False,
    "displayModeBar": "hover", "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "sendChartToCloud"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "topojsonURL": "/assets/geo/",
}


def graph(identifier: str) -> dcc.Graph:
    heights = {"map-chart": 450, "monthly-chart": 290, "violent-chart": 330,
               "lowest-chart": 285, "sex-chart": 720, "age-chart": 380}
    return dcc.Graph(id=identifier, config=GRAPH_CONFIG, className="chart", responsive=True,
                     style={"height": f"{heights[identifier]}px"})


def panel(title: str, subtitle: str, content, *, number: str, class_name: str = "", footer=None):
    return html.Section([
        html.Div([
            html.Div([html.H3(title), html.P(subtitle, className="panel-subtitle")]),
            html.Span(number, className="panel-number", **{"aria-hidden": "true"}),
        ], className="panel-heading"),
        html.Div(content) if isinstance(content, list) else content,
        html.Div(footer, className="panel-footer") if footer else None,
    ], className=f"panel {class_name}")


def metric_card(identifier: str, title: str, detail: str, accent: bool = False):
    return html.Div([
        html.P(title, className="metric-label"),
        html.Div("—", id=identifier, className="metric-value"),
        html.P(detail, className="metric-detail"),
    ], className="metric-card" + (" metric-primary" if accent else ""))

