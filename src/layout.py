"""Application layout and static methodological context."""

from dash import dcc, html

from src.components.cards import graph, metric_card, panel
from src.data.repository import Dataset
from src.settings import AGE_GROUPS, MONTHS, SEX_LABELS


def field(label: str, identifier: str, options: list, value, *, multi: bool = False):
    return html.Div([
        html.Label(label, htmlFor=identifier),
        dcc.Dropdown(id=identifier, options=options, value=value, multi=multi,
                     clearable=multi, searchable=True, placeholder="Todo el año" if multi else "Seleccionar",
                     labels={"select_all": "Seleccionar todos", "deselect_all": "Quitar selección",
                             "selected_count": "{num_selected} seleccionados",
                             "search": "Buscar", "clear_search": "Borrar búsqueda",
                             "clear_selection": "Limpiar selección", "no_options_found": "Sin resultados"},
                     className="filter-select"),
    ], className="filter-field")


def sidebar(dataset: Dataset):
    departments = [{"label": "Todo Colombia", "value": "all"}] + [
        {"label": r.department_name, "value": r.department} for r in dataset.departments.itertuples()
    ]
    return html.Aside([
        html.A([html.Span("V", className="brand-symbol"), html.Span(["VITAL", html.Small("COLOMBIA")])], href="#inicio", className="brand", **{"aria-label": "Vital Colombia, inicio"}),
        html.Div("OBSERVATORIO · 2019", className="sidebar-eyebrow"),
        html.Nav([
            html.A([html.Span("01"), "Panorama general"], href="#panorama", className="nav-link"),
            html.A([html.Span("02"), "Territorios"], href="#territorios", className="nav-link"),
            html.A([html.Span("03"), "Causas de muerte"], href="#causas", className="nav-link"),
            html.A([html.Span("04"), "Perfil demográfico"], href="#demografia", className="nav-link"),
        ], **{"aria-label": "Secciones del análisis"}),
        html.Div([
            html.Div([html.H2("Explora los datos"), html.Span("FILTROS")], className="filter-title"),
            field("Departamento", "filter-department", departments, "all"),
            field("Meses", "filter-months", [{"label": name, "value": i} for i, name in enumerate(MONTHS, 1)], [], multi=True),
            field("Sexo registrado", "filter-sex", [{"label": "Todos", "value": "all"}] + [{"label": name, "value": str(code)} for code, name in SEX_LABELS.items()], "all"),
            field("Grupo de edad", "filter-age", [{"label": "Todas las edades", "value": "all"}] + [{"label": f"{group[0]} · {group[1]}", "value": str(i)} for i, group in enumerate(AGE_GROUPS)], "all"),
            html.Button("Restablecer filtros", id="reset-filters", n_clicks=0, className="reset-button"),
            html.P("Los filtros actualizan todo el tablero. Sin meses seleccionados, se muestra el año completo.", className="filter-help"),
        ], className="filter-box"),
        html.Div([
            html.Span(className="source-dot"), html.Span("DATOS DANE"),
            html.P("Estadísticas vitales\nDefunciones no fetales"),
            html.A("Fuentes y metodología ↗", href="#metodologia"),
        ], className="sidebar-source"),
    ], className="sidebar")


def methodology(dataset: Dataset):
    return html.Details([
        html.Summary([html.Span("Cómo leer este observatorio"), html.Span("Fuentes, criterios y alcance +")]),
        html.Div([
            html.Div([
                html.H3("Una lectura responsable"),
                html.P("Se cuentan defunciones no fetales de 2019. Los valores son cantidades absolutas; los archivos no incluyen población para calcular tasas de mortalidad o riesgo."),
                html.P("La ubicación corresponde al código territorial del anexo académico. La estructura es compatible con los campos de ocurrencia de la defunción del DANE; no se interpreta como residencia ni como lugar de la agresión. Un fallecimiento en un hospital puede registrarse lejos del lugar del hecho."),
                html.P("Los rankings incluyen únicamente territorios de tipo Municipio en Divipola y con registros positivos bajo los filtros activos. Los empates se resuelven por código DANE ascendente. La ausencia de registros no se interpreta como cero muertes."),
            ]),
            html.Div([
                html.H3("Criterios del análisis"),
                html.P("X95 incluye todas sus subcategorías (por ejemplo, X954 y X959). Representa agresiones con disparo de otras armas de fuego y las no especificadas. No equivale a todos los homicidios."),
                html.P("El gráfico circular muestra cantidades y porcentajes dentro de los diez municipios seleccionados, no porcentajes nacionales ni tasas. Si hay menos de diez municipios elegibles se muestran los disponibles."),
                html.P("La tabla de causas conserva el código CIE-10 completo del anexo. Las edades se agrupan según la referencia académica: 0–4, 5–6, 7–8, 9–10, 11, 12–13, 14–16, 17–19, 20–24, 25–28 y 29. Son categorías de amplitud desigual; la altura indica frecuencia, no densidad por año de edad."),
                html.P("Los nombres neonatal e infantil se usan según la tabla de la actividad; no representan tasas epidemiológicas. Se conservan sexo indeterminado y edad desconocida."),
            ]),
            html.Div([
                html.H3("Fuentes y trazabilidad"),
                html.Ul([
                    html.Li(html.A("DANE · Estadísticas vitales 2019", href="https://microdatos.dane.gov.co/index.php/catalog/696", target="_blank", rel="noopener noreferrer")),
                    html.Li("Anexo 1: defunciones no fetales; Anexo 2: catálogo CIE-10; Divipola: nombres y tipos territoriales."),
                    html.Li(html.A("DANE · Servicio cartográfico MGN 2019", href="https://portalgis.dane.gov.co/mparcgis/rest/services/MGN2019/Serv_CapasMGN_2019/FeatureServer/319", target="_blank", rel="noopener noreferrer")),
                ]),
                html.P(f"Control de calidad: {dataset.quality['records']:,} registros conservados; códigos territoriales y causas asociados a sus catálogos. Geometría simplificada del servicio MGN 2019; sus atributos indican versión de límites 2018.".replace(",", ".")),
                html.P("Fuente: Departamento Administrativo Nacional de Estadística — www.dane.gov.co. Elaboración académica propia; no es un producto oficial del DANE."),
            ]),
        ], className="methodology-grid"),
    ], id="metodologia", className="methodology")


def create_layout(dataset: Dataset):
    return html.Div([
        html.A("Saltar al contenido", href="#contenido", className="skip-link"),
        sidebar(dataset),
        html.Main([
            html.Header([
                html.Div([html.Span("Análisis de población", className="breadcrumb"), html.Span(" / "), html.Strong("Mortalidad")]),
                html.Div([html.Span("EDICIÓN 2019", className="edition"), html.Button("↓  Descargar datos", id="download-button", n_clicks=0, className="download-button")]),
            ], className="topbar"),
            html.Div([
                html.Section([
                    html.Div([
                        html.Div([html.Span(className="tiny-dot"), "ESTADÍSTICAS VITALES"], className="eyebrow"),
                        html.H1(["Mortalidad en ", html.Span("Colombia.")]),
                        html.P("Una mirada a las defunciones de 2019: su distribución en el territorio, sus causas y las etapas de la vida.", className="hero-description"),
                    ]),
                    html.Div([html.Span("PERÍODO DE ANÁLISIS"), html.Strong("2019"), html.Small("Enero — diciembre")], className="year-stamp"),
                ], id="inicio", className="hero"),
                html.Div([html.Span("VISTA ACTUAL", className="scope-label"), html.Span(id="selection-description"), html.Span("DATOS NO FETALES", className="scope-type")], className="selection-bar", role="status", **{"aria-live": "polite"}),
                html.Div(id="empty-notice", role="status"),
                dcc.Loading([
                    html.Section([
                        metric_card("metric-total", "Defunciones registradas", "Total de la selección", True),
                        metric_card("metric-x95", "Agresiones con armas · X95", "Subconjunto de las defunciones"),
                        metric_card("metric-departments", "Departamentos con registros", "Incluye Bogotá D. C."),
                        metric_card("metric-older", "Personas de 60 años o más", "Porcentaje del total seleccionado"),
                    ], className="metrics", id="panorama"),
                    html.Div([html.H2("El territorio y el tiempo"), html.Span("DISTRIBUCIÓN DE LAS DEFUNCIONES")], className="section-heading"),
                    html.Div([
                        panel("Un país, distintas realidades", "Defunciones por departamento", graph("map-chart"), number="01", footer="Escala absoluta · Gris: fuera de la selección o sin registros · Incluye el archipiélago de San Andrés"),
                        panel("El año, mes a mes", "Evolución de las defunciones registradas", [graph("monthly-chart"), html.Div(id="monthly-insight", className="insight")], number="02", footer="Las cantidades mensuales no están ajustadas por el número de días."),
                    ], className="grid overview-grid"),
                    html.Div([html.H2("Una mirada a los municipios"), html.Span("COMPARACIONES EN EL ÁMBITO SELECCIONADO")], id="territorios", className="section-heading"),
                    html.Div([
                        panel("Mayor número de agresiones X95", "Hasta 5 municipios · Otras armas de fuego y las no especificadas", graph("violent-chart"), number="03", footer="Cantidad de defunciones X95. No es una tasa de violencia ni el total de homicidios."),
                        panel("Menor número de defunciones", "Hasta 10 municipios con registros positivos", html.Div([graph("lowest-chart"), html.Div(id="lowest-legend", className="donut-legend")], className="donut-body"), number="04", footer="Los porcentajes corresponden solo a estos municipios. Empates: código DANE ascendente."),
                    ], className="grid equal-grid"),
                    html.Div([html.H2("Las causas detrás de las cifras"), html.Span("CLASIFICACIÓN INTERNACIONAL DE ENFERMEDADES")], id="causas", className="section-heading"),
                    panel("Diez principales causas de muerte", "Código CIE-10 completo · Orden descendente por número de casos", html.Div(html.Table([
                        html.Thead(html.Tr([html.Th("#"), html.Th("Código"), html.Th("Causa de muerte"), html.Th("Defunciones", className="numeric"), html.Th("% del total", className="numeric")])),
                        html.Tbody(id="causes-table"),
                    ], className="causes-table"), className="table-scroll"), number="05", footer="Cada registro aporta una causa del anexo. El porcentaje se calcula sobre todas las defunciones de la selección."),
                    html.Div([html.H2("Las etapas de la vida"), html.Span("PERFIL DEMOGRÁFICO")], id="demografia", className="section-heading"),
                    html.Div([
                        panel("Defunciones por sexo", "Comparación entre departamentos", graph("sex-chart"), number="06", footer="Sexo registrado: masculino, femenino e indeterminado. La suma conserva el total seleccionado."),
                        html.Div([
                            panel("Distribución por edad", "Frecuencias de los grupos definidos en la actividad", graph("age-chart"), number="07", footer="Grupos de amplitud desigual. La categoría «Sin información» se presenta por separado."),
                            html.Div([html.Span("PARA INTERPRETAR"), html.H3("Las cifras cuentan una parte de la historia."), html.P("Más defunciones no implica una mayor probabilidad de morir. El tamaño de la población, su composición por edad y la atención hospitalaria también influyen en los conteos."), html.A("Conoce los criterios del análisis ↗", href="#metodologia")], className="reading-note"),
                        ], className="demographic-right"),
                    ], className="grid equal-grid"),
                ], type="circle", color="#168b86", delay_show=250),
                methodology(dataset),
                html.Footer([html.Div([html.Strong("VITAL / COLOMBIA"), html.Span("Mortalidad no fetal · 2019")]), html.Span("Proyecto académico · Python + Dash + Plotly")], className="footer"),
            ], className="content", id="contenido"),
        ], className="main"),
        dcc.Download(id="download-data"),
    ], className="app-shell")
