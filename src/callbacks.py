"""Bind interface events to the analytical functions."""

from dash import Input, Output, State, dcc, html

from src import figures
from src.analytics import Filters, filter_data, format_count, format_percent, metrics, monthly_counts, municipality_ranking, top_causes
from src.data.repository import Dataset
from src.settings import AGE_GROUPS, MONTHS, SEX_LABELS


def selection_text(dataset: Dataset, filters: Filters) -> str:
    departments = dict(zip(dataset.departments.department, dataset.departments.department_name))
    period = ", ".join(MONTHS[m - 1][:3] for m in sorted(filters.months)) if filters.months else "Todo 2019"
    sex = SEX_LABELS[int(filters.sex)] if filters.sex != "all" else "Todos los sexos"
    age = AGE_GROUPS[int(filters.age_group)][1] if filters.age_group != "all" else "Todas las edades"
    return " · ".join([departments.get(filters.department, "Colombia"), period, sex, age])


def dashboard_values(dataset: Dataset, filters: Filters) -> tuple:
    frame = filter_data(dataset.frame, filters)
    stats = metrics(frame)
    ranking = municipality_ranking(frame, lowest=True)
    legend = [html.Div([
        html.Span(className="legend-dot", style={"backgroundColor": figures.PIE_COLORS[i]}),
        html.Span([html.Strong(r.municipality_name), html.Small(r.department_name)], className="legend-place"),
        html.Span(format_count(r.deaths), className="legend-value"),
    ], className="legend-row") for i, r in enumerate(ranking.itertuples())]
    table = [html.Tr([
        html.Td(f"{i:02}", className="rank-cell"),
        html.Td(html.Span(r.cause, className="code-badge")),
        html.Td(r.description), html.Td(format_count(r.deaths), className="numeric count-cell"),
        html.Td(format_percent(r.share * 100), className="numeric"),
    ]) for i, r in enumerate(top_causes(frame, dataset.causes).itertuples(), 1)]
    if not table:
        table = [html.Tr(html.Td("No hay causas registradas para esta selección.", colSpan=5, className="table-empty"))]
    monthly = monthly_counts(frame, filters.months)
    if stats["total"]:
        peak = int(monthly.idxmax())
        insight = [html.Span("EL MES CON MÁS REGISTROS"), html.Strong(f"{MONTHS[peak - 1]} · {format_count(monthly.max())}"), html.P("Dentro del período y los filtros seleccionados.")]
        notice = None
    else:
        insight = [html.P("Cambia los filtros para explorar otras combinaciones.")]
        notice = html.Div("No se encontraron registros para esta combinación. Prueba otros filtros o restablece la vista nacional.", className="empty-banner")
    return (
        format_count(stats["total"]), format_count(stats["x95"]), str(stats["departments"]),
        format_percent(stats["older_share"]) if stats["older_share"] is not None else "—",
        selection_text(dataset, filters), notice,
        figures.department_map(frame, dataset.geography), figures.monthly_line(frame, filters.months),
        figures.violent_cities(frame), figures.lowest_cities(frame),
        figures.sex_by_department(frame), figures.age_histogram(frame), table, legend, insight,
    )


def register_callbacks(app, dataset: Dataset) -> None:
    filters = [Input("filter-department", "value"), Input("filter-months", "value"), Input("filter-sex", "value"), Input("filter-age", "value")]

    @app.callback(
        Output("metric-total", "children"), Output("metric-x95", "children"),
        Output("metric-departments", "children"), Output("metric-older", "children"),
        Output("selection-description", "children"), Output("empty-notice", "children"),
        Output("map-chart", "figure"), Output("monthly-chart", "figure"),
        Output("violent-chart", "figure"), Output("lowest-chart", "figure"),
        Output("sex-chart", "figure"), Output("age-chart", "figure"),
        Output("causes-table", "children"), Output("lowest-legend", "children"),
        Output("monthly-insight", "children"), *filters,
    )
    def update_dashboard(department, months, sex, age):
        return dashboard_values(dataset, Filters(department or "all", tuple(months or ()), sex or "all", age or "all"))

    @app.callback(
        Output("filter-department", "value"), Output("filter-months", "value"),
        Output("filter-sex", "value"), Output("filter-age", "value"),
        Input("reset-filters", "n_clicks"), prevent_initial_call=True,
    )
    def reset_filters(_clicks):
        return "all", [], "all", "all"

    @app.callback(
        Output("download-data", "data"), Input("download-button", "n_clicks"),
        State("filter-department", "value"), State("filter-months", "value"),
        State("filter-sex", "value"), State("filter-age", "value"), prevent_initial_call=True,
    )
    def download_selection(_clicks, department, months, sex, age):
        selected = filter_data(dataset.frame, Filters(department or "all", tuple(months or ()), sex or "all", age or "all"))
        columns = ["department", "department_name", "municipality", "municipality_name", "territory_type", "month", "sex", "age_code", "cause", "deaths"]
        export = selected[columns].copy()
        export.columns = ["codigo_departamento", "departamento", "codigo_dane", "municipio", "tipo_territorio", "mes", "sexo_codigo", "grupo_edad1", "codigo_causa", "defunciones"]
        # Semicolon + BOM makes the summary directly usable in Spanish Excel.
        content = "\ufeff" + export.to_csv(index=False, sep=";")
        return dcc.send_string(content, "mortalidad_colombia_2019_seleccion.csv", type="text/csv;charset=utf-8")

