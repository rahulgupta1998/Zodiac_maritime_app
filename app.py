import os
import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px

from database.db import initialize_database, load_reports, save_report_changes
from services.validation import validate_changes
from services.data_service import FILTER_COLUMNS, NUMERIC_COLUMNS

APP_TITLE = "Zodiac Maritime – Vessel KPI Analytics Dashboard"

# Initialize the local SQLite store from the supplied CSV the first time the app runs.
initialize_database()

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Zodiac Maritime KPI Dashboard",
    suppress_callback_exceptions=True,
)
server = app.server


def get_df() -> pd.DataFrame:
    return load_reports()


def option_values(df, column):
    if df.empty:
        return []
    return [
        {"label": str(v), "value": str(v)}
        for v in sorted(df[column].dropna().astype(str).unique())
    ]


def filter_df(df, vessels, start_date, end_date, kpis, voyages):
    dff = df.copy()
    if dff.empty:
        return dff

    if vessels:
        dff = dff[dff["Vessel_Name"].isin(vessels)]
    if start_date:
        dff = dff[dff["To_Timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        end = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        dff = dff[dff["To_Timestamp"] < end]
    if kpis:
        dff = dff[dff["KPI"].isin(kpis)]
    if voyages:
        dff = dff[dff["Voyage_Type"].isin(voyages)]
    return dff


def build_scatter(df, value_col, flag_col, title):
    dff = df.dropna(subset=[value_col]).copy()
    if dff.empty:
        fig = px.scatter(title=title)
        fig.update_layout(template="plotly_white")
        return fig

    fig = px.scatter(
        dff,
        x="To_Timestamp",
        y=value_col,
        color=flag_col,
        custom_data=["row_id", "Report_ID"],
        title=title,
        labels={value_col: value_col, "To_Timestamp": "Report date"},
        color_discrete_map={"No": "#2F6FED", "Yes": "#F59E0B"},
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=55, r=25, t=55, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8fbff",
        font=dict(family="Inter, Arial, sans-serif", color="#1f2937"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.75)"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#e6edf5",
            zeroline=False,
            title_font=dict(size=13, color="#475467"),
            tickfont=dict(size=11, color="#667085")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#e6edf5",
            zeroline=False,
            title_font=dict(size=13, color="#475467"),
            tickfont=dict(size=11, color="#667085")
        )
    )
    fig.update_traces(marker=dict(size=10, line=dict(width=1, color="white"), opacity=0.88))
    return fig


def table_columns():
    editable = {"Power_%", "Speed_%"}
    cols = [
        ("Report_ID", "Report ID"),
        ("Vessel_Name", "Vessel"),
        ("To_Timestamp", "Timestamp"),
        ("KPI", "KPI"),
        ("Voyage_Type", "Voyage"),
        ("Power_%", "Power %"),
        ("Power_Deviation", "Power deviation"),
        ("Power_Filter_Flag", "Power flag"),
        ("Speed_%", "Speed %"),
        ("Speed_Deviation", "Speed deviation"),
        ("Speed_Filter", "Speed flag"),
        ("row_id", "Internal row id"),
    ]

    definitions = []
    for field, header in cols:
        col = {
            "field": field,
            "headerName": header,
            "sortable": True,
            "filter": True,
            "resizable": True,
        }
        if field in editable:
            col["editable"] = True
            col["valueParser"] = {"function": "Number(params.newValue)"}
        else:
            col["editable"] = False
        if field in {"Power_Deviation", "Speed_Deviation"}:
            col["cellStyle"] = {
                "styleConditions": [
                    {
                        "condition": "params.value < 0",
                        "style": {"color": "#b00020", "fontWeight": "700", "backgroundColor": "#fde7e7"},
                    }
                ]
            }
        if field == "row_id":
            col["hide"] = True
        definitions.append(col)
    return definitions


initial_df = get_df()
initial_min = initial_df["To_Timestamp"].min().date() if not initial_df.empty else None
initial_max = initial_df["To_Timestamp"].max().date() if not initial_df.empty else None

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div("ZODIAC MARITIME", className="eyebrow"),
                            html.H1("Vessel KPI Analytics", className="page-title"),
                            html.P(
                                "Monitor performance, spot anomalies, and safely correct report data.",
                                className="page-subtitle",
                            ),
                        ],
                        className="hero-content",
                    ),
                ],
                width=12,
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Span("01", className="section-number"),
                            html.H5("Filters", className="section-title"),
                        ],
                        className="section-heading",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [html.Label("Vessel"), dcc.Dropdown(id="vessel-filter", options=option_values(initial_df, "Vessel_Name"), multi=True, placeholder="All vessels")],
                                md=3,
                            ),
                            dbc.Col(
                                [html.Label("Date range"), dcc.DatePickerRange(id="date-filter", start_date=initial_min, end_date=initial_max, display_format="DD-MMM-YYYY")],
                                md=3,
                            ),
                            dbc.Col(
                                [html.Label("KPI"), dcc.Dropdown(id="kpi-filter", options=[{"label": x, "value": x} for x in ["Power", "Speed"]], value=["Power", "Speed"], multi=True)],
                                md=3,
                            ),
                            dbc.Col(
                                [html.Label("Voyage type"), dcc.Dropdown(id="voyage-filter", options=[{"label": x, "value": x} for x in ["CARGO", "BALLAST"]], value=["CARGO", "BALLAST"], multi=True)],
                                md=3,
                            ),
                        ],
                        className="g-3",
                    ),
                ]
            ),
            className="mb-4 dashboard-card filter-card",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Span("02", className="section-number"),
                                        html.H5("Power % vs. report date", className="section-title"),
                                    ],
                                    className="section-heading",
                                ),
                                dcc.Graph(id="power-chart", style={"height": "420px"}),
                            ]
                        ),
                        className="dashboard-card chart-card power-card",
                    ),
                    md=6,
                    className="mb-4",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Span("03", className="section-number"),
                                        html.H5("Speed % vs. report date", className="section-title"),
                                    ],
                                    className="section-heading",
                                ),
                                dcc.Graph(id="speed-chart", style={"height": "420px"}),
                            ]
                        ),
                        className="dashboard-card chart-card speed-card",
                    ),
                    md=6,
                    className="mb-4",
                ),
            ]
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Span("04", className="section-number"),
                                        html.H5("Detail table", className="section-title"),
                                    ],
                                    className="section-heading",
                                ),
                                md=8,
                            ),
                            dbc.Col(html.Div(id="selection-summary", className="text-end text-muted"), md=4),
                        ]
                    ),
                    dag.AgGrid(
                        id="detail-grid",
                        rowData=[],
                        columnDefs=table_columns(),
                        defaultColDef={"minWidth": 120, "sortable": True, "filter": True, "resizable": True},
                        dashGridOptions={
                            "animateRows": False,
                            "pagination": True,
                            "paginationPageSize": 25,
                            "getRowId": "params.data.row_id",
                        },
                        columnSize="responsiveSizeToFit",
                        style={"height": "560px", "width": "100%"},
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dbc.Button("Save changes", id="save-button", color="primary", className="mt-3"), width="auto"),
                            dbc.Col(html.Div(id="save-status", className="mt-3"), width=True),
                        ],
                        className="align-items-center",
                    ),
                    html.Small(
                        "Editable fields: Power % and Speed %. Select chart points using click, box-select or lasso-select.",
                        className="text-muted d-block mt-2",
                    ),
                ]
            ),
            className="mb-5 dashboard-card detail-card",
        ),
    ],
    fluid=True,
    className="app-shell",
)


@callback(
    Output("power-chart", "figure"),
    Output("speed-chart", "figure"),
    Input("vessel-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
    Input("kpi-filter", "value"),
    Input("voyage-filter", "value"),
)
def update_charts(vessels, start_date, end_date, kpis, voyages):
    df = get_df()
    dff = filter_df(df, vessels, start_date, end_date, kpis, voyages)
    power_df = dff[dff["KPI"] == "Power"]
    speed_df = dff[dff["KPI"] == "Speed"]
    return (
        build_scatter(power_df, "Power_%", "Power_Filter_Flag", "Power %"),
        build_scatter(speed_df, "Speed_%", "Speed_Filter", "Speed %"),
    )


@callback(
    Output("detail-grid", "rowData"),
    Output("selection-summary", "children"),
    Input("power-chart", "selectedData"),
    Input("speed-chart", "selectedData"),
    Input("vessel-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
    Input("kpi-filter", "value"),
    Input("voyage-filter", "value"),
)
def update_table(power_selected, speed_selected, vessels, start_date, end_date, kpis, voyages):
    df = get_df()
    dff = filter_df(df, vessels, start_date, end_date, kpis, voyages)

    selected_ids = []
    for selection in (power_selected, speed_selected):
        if selection and selection.get("points"):
            for point in selection["points"]:
                custom = point.get("customdata") or []
                if custom:
                    selected_ids.append(custom[0])

    selected_ids = list(dict.fromkeys(selected_ids))
    if selected_ids:
        dff = dff[dff["row_id"].isin(selected_ids)]
        message = f"{len(dff)} selected report row(s)"
    else:
        message = f"Showing all {len(dff)} row(s) matching the filters"

    columns = [
        "row_id", "Report_ID", "Vessel_Name", "To_Timestamp", "KPI", "Voyage_Type",
        "Power_%", "Power_Deviation", "Power_Filter_Flag",
        "Speed_%", "Speed_Deviation", "Speed_Filter"
    ]
    if dff.empty:
        return [], message

    display = dff[columns].copy()
    display["To_Timestamp"] = display["To_Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display = display.where(pd.notna(display), None)
    return display.to_dict("records"), message


@callback(
    Output("save-status", "children"),
    Input("save-button", "n_clicks"),
    State("detail-grid", "rowData"),
    prevent_initial_call=True,
)
def save_changes(n_clicks, rows):
    if not rows:
        return dbc.Alert("There are no rows to save.", color="warning", className="mb-0")

    errors = validate_changes(rows)
    if errors:
        return dbc.Alert(
            [html.Div("Save blocked. Please correct the following:"), html.Ul([html.Li(e) for e in errors])],
            color="danger",
            className="mb-0",
        )

    try:
        changed_count = save_report_changes(rows, user=os.getenv("APP_USER", "assessment_user"))
        if changed_count == 0:
            return dbc.Alert("No changes detected.", color="secondary", className="mb-0")
        return dbc.Alert(f"Saved {changed_count} field change(s) and recorded them in the audit log.", color="success", className="mb-0")
    except Exception as exc:
        return dbc.Alert(f"Save failed: {exc}", color="danger", className="mb-0")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8050"))
    app.run(debug=True, host="127.0.0.1", port=port)
