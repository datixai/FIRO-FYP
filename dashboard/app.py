import os
import json
import time
from datetime import datetime
from flask import jsonify, send_from_directory

# ============================================================
# 🔑  SINGLE SOURCE OF TRUTH: service_account_key.json
#     All credentials — admin SDK + Firebase client config —
#     are loaded from this ONE file. Never hardcode anything.
# ============================================================

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
KEY_PATH   = os.environ.get("GCP_KEY_PATH", os.path.join(BASE_DIR, "service_account_key.json"))

def load_service_key():
    """Load service_account_key.json and return its contents as a dict."""
    if not os.path.exists(KEY_PATH):
        print(f"[FIRO] ⚠️  Key file not found at: {KEY_PATH}")
        print("[FIRO]    Copy service_account_key.example.json → service_account_key.json and fill it in.")
        return {}
    with open(KEY_PATH, "r") as f:
        return json.load(f)

SERVICE_KEY = load_service_key()

# --- Admin SDK project config (used by google-cloud-firestore) ---
PROJECT_ID = SERVICE_KEY.get("project_id", "")

# --- Client-side Firebase config (safe to serve to browser) ---
# Stored under "firebase_client" key in service_account_key.json
CLIENT_CONFIG = SERVICE_KEY.get("firebase_client", {})

if not CLIENT_CONFIG:
    print("[FIRO] ⚠️  'firebase_client' section missing from service_account_key.json")
    print("[FIRO]    See service_account_key.example.json for the required structure.")

# ============================================================
#  FIRESTORE CLIENT (google-cloud-firestore / admin SDK)
# ============================================================

try:
    from google.cloud import firestore
    from google.cloud.firestore import Query, FieldFilter
except ImportError:
    firestore = None
    class Query:
        DESCENDING = "DESCENDING"
    class FieldFilter:
        def __init__(self, *args, **kwargs): pass

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

FIRESTORE_COLLECTION_NAME = "fire_logs"
POLLING_INTERVAL_MS       = 5000
FIRE_THRESHOLD            = 0.70

db = None
if firestore and PROJECT_ID:
    try:
        db = firestore.Client.from_service_account_json(KEY_PATH, project=PROJECT_ID)
        print(f"[FIRO] ✅  Firestore connected — project: {PROJECT_ID}")
    except Exception as e:
        print(f"[FIRO] ⚠️  Firestore init failed: {e}")

# ============================================================
#  DASH APPLICATION
# ============================================================

app = dash.Dash(
    __name__,
    external_stylesheets=["https://unpkg.com/tailwindcss@2.2.19/dist/tailwind.min.css"],
    suppress_callback_exceptions=True,
)

# Expose the underlying Flask server so we can add routes to it
server = app.server

# ============================================================
#  FLASK ROUTES — serve HTML pages + firebase config endpoint
# ============================================================

@server.route("/")
@server.route("/index")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")

@server.route("/login")
def serve_login():
    return send_from_directory(BASE_DIR, "login.html")

@server.route("/logs")
def serve_logs():
    return send_from_directory(BASE_DIR, "logs.html")

@server.route("/settings")
def serve_settings():
    return send_from_directory(BASE_DIR, "settings.html")

@server.route("/<path:filename>")
def serve_static(filename):
    """Serve any other static asset (logo, CSS, JS, manifest, etc.)"""
    return send_from_directory(BASE_DIR, filename)

@server.route("/api/firebase-config")
def firebase_config_endpoint():
    """
    Returns ONLY the client-safe Firebase config from service_account_key.json.
    Private keys are NEVER exposed — only the firebase_client section is returned.
    """
    if not CLIENT_CONFIG:
        return jsonify({"error": "firebase_client config not found in service_account_key.json"}), 500
    return jsonify(CLIENT_CONFIG)

# ============================================================
#  DATA FETCHING
# ============================================================

def get_latest_fire_data():
    """Fetches the latest 50 fire logs from Firestore (last 1 hour)."""
    REQUIRED_COLUMNS = [
        "timestamp", "timestamp_str", "coords_x", "coords_y",
        "fire_probability", "cameraLocation", "severity",
    ]
    if not db:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    collection_path = f"artifacts/{PROJECT_ID}/public/data/{FIRESTORE_COLLECTION_NAME}"
    try:
        one_hour_ago_ms = int(time.time() * 1000) - (60 * 60 * 1000)
        query = (
            db.collection(collection_path)
            .where(filter=FieldFilter("timestamp_ms", ">=", one_hour_ago_ms))
            .order_by("timestamp_ms", direction=Query.DESCENDING)
            .limit(50)
        )
        docs = query.stream()
        data = []
        for doc in docs:
            log = doc.to_dict()
            try:
                ts_ms = log.get("timestamp_ms", int(time.time() * 1000))
                ts_str = log.get(
                    "timestamp_str",
                    datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                )
                data.append({
                    "timestamp":        ts_ms,
                    "timestamp_str":    ts_str,
                    "coords_x":         float(log.get("coords_x", 0)),
                    "coords_y":         float(log.get("coords_y", 0)),
                    "fire_probability": float(log.get("fire_probability", 0)),
                    "cameraLocation":   log.get("camera_location", "Unknown"),
                    "severity":         log.get("detection_class", "N/A"),
                })
            except (ValueError, TypeError):
                continue

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        return df.sort_values("timestamp", ascending=False).drop_duplicates(subset=["cameraLocation"])

    except Exception as e:
        print(f"[FIRO] Firestore fetch error: {e}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

# ============================================================
#  DASH LAYOUT  (analytics panel — mounted at /dash/)
# ============================================================

DARK = {
    "bgcolor":        "#161b22",
    "paper_bgcolor":  "#161b22",
    "plot_bgcolor":   "#161b22",
    "font":           {"color": "#e6e6e6"},
}

app.layout = html.Div(
    className="p-6 min-h-screen bg-gray-900 text-white font-sans",
    children=[
        dcc.Interval(id="interval-component", interval=POLLING_INTERVAL_MS, n_intervals=0),

        html.Div(
            className="flex justify-between items-center pb-4 border-b border-gray-700 mb-4",
            children=[
                html.H1("FIRO — Analytics Dashboard (Last Hour)",
                        className="text-3xl font-bold text-cyan-400 tracking-wider"),
                html.Div(className="flex items-center space-x-4", children=[
                    html.Span(id="connection-status",
                              className="text-sm font-medium px-3 py-1 rounded-full bg-green-900 text-green-300"),
                    html.P(id="last-updated-time", className="text-sm text-gray-400"),
                ]),
            ],
        ),

        html.Div(
            className="grid grid-cols-1 lg:grid-cols-3 gap-6",
            style={"minHeight": "80vh"},
            children=[
                # Map
                html.Div(
                    className="lg:col-span-2 rounded-xl bg-gray-800 shadow-xl overflow-hidden",
                    children=[dcc.Graph(id="fire-map", config={"displayModeBar": False},
                                       style={"height": "100%"})],
                ),
                # Sidebar
                html.Div(
                    className="lg:col-span-1 flex flex-col space-y-6 overflow-y-auto",
                    children=[
                        html.Div(
                            id="alert-panel",
                            className="p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-gray-800",
                            children=[
                                html.Div(id="alert-icon-container"),
                                html.H2(id="alert-header",
                                        className="text-3xl font-extrabold tracking-tight text-white mb-1"),
                                html.P(id="alert-message", className="text-sm text-gray-400"),
                            ],
                        ),
                        html.Div(
                            className="flex-grow flex flex-col rounded-xl bg-gray-800 shadow-xl p-6 overflow-y-auto",
                            children=[
                                html.H3("RECENT LOG HISTORY (Last 60 Mins)",
                                        className="text-xl font-semibold mb-3 text-cyan-400 border-b border-gray-700 pb-2"),
                                html.Div(id="log-table-container", className="overflow-y-auto flex-grow"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# ============================================================
#  DASH CALLBACK
# ============================================================

@app.callback(
    [
        Output("fire-map",              "figure"),
        Output("alert-panel",           "className"),
        Output("alert-icon-container",  "children"),
        Output("alert-header",          "children"),
        Output("alert-message",         "children"),
        Output("log-table-container",   "children"),
        Output("last-updated-time",     "children"),
        Output("connection-status",     "children"),
        Output("connection-status",     "className"),
    ],
    [Input("interval-component", "n_intervals")],
)
def update_dashboard(n):
    df = get_latest_fire_data()

    status_msg   = "No Data"
    status_cls   = "text-sm font-medium px-3 py-1 rounded-full bg-yellow-900 text-yellow-300"
    updated_text = "N/A"
    panel_cls    = "p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-gray-800"
    icon         = html.Span("✅", style={"fontSize": "4rem"})
    header_text  = "ALL SYSTEMS GREEN"
    msg_text     = "No fire threat detected in the last hour."
    table_out    = html.P("No data.", className="text-center py-4 text-gray-500 text-sm")

    fig = go.Figure(layout=go.Layout(
        **DARK, height=700,
        mapbox=dict(style="carto-darkmatter", center=dict(lat=33.73, lon=73.08), zoom=8),
    ))

    if df.empty:
        if not db:
            status_msg  = "DB Disconnected"
            status_cls  = "text-sm font-medium px-3 py-1 rounded-full bg-red-900/50 text-red-300"
            header_text = "DB NOT CONNECTED"
            msg_text    = "Check service_account_key.json and restart."
        return fig, panel_cls, icon, header_text, msg_text, table_out, updated_text, status_msg, status_cls

    df["fire_probability"] = pd.to_numeric(df["fire_probability"], errors="coerce").fillna(0)
    df["is_fire"]          = df["fire_probability"] >= FIRE_THRESHOLD
    df["color"]            = df["is_fire"].apply(lambda x: "red" if x else "green")
    df["size"]             = df["fire_probability"].apply(lambda x: max(10, x * 30))

    max_row = df.loc[df["fire_probability"].idxmax()]

    fig = px.scatter_mapbox(
        df, lat="coords_x", lon="coords_y",
        hover_name="cameraLocation",
        hover_data={"fire_probability": ":.2f", "severity": True, "coords_x": False, "coords_y": False},
        color="color",
        color_discrete_map={"red": "red", "green": "lime"},
        size="size", size_max=30, zoom=8,
        center={"lat": df["coords_x"].mean(), "lon": df["coords_y"].mean()},
    )
    fig.update_layout(**DARK, mapbox_style="carto-darkmatter", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(marker=dict(opacity=0.8))

    if max_row["is_fire"]:
        prob_pct   = f"{max_row['fire_probability'] * 100:.1f}%"
        panel_cls  = "p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-red-900/50 animate-pulse"
        icon       = html.Span("🔥", style={"fontSize": "4rem"})
        header_text = "⚠️  FIRE DETECTED"
        msg_text   = f"{max_row.get('cameraLocation', 'Unknown')} — {prob_pct} probability"

    table_df  = df.head(5)[["timestamp_str", "cameraLocation", "fire_probability", "is_fire"]]
    table_out = dash_table.DataTable(
        columns=[
            {"name": "Time",     "id": "timestamp_str",   "type": "text"},
            {"name": "Location", "id": "cameraLocation",  "type": "text"},
            {"name": "Prob.",    "id": "fire_probability","type": "numeric",
             "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.percentage)},
        ],
        data=table_df.to_dict("records"),
        hidden_columns=["is_fire"],
        style_header={"backgroundColor": "#30363d", "color": "white", "fontWeight": "bold"},
        style_data_conditional=[{
            "if": {"filter_query": "{is_fire} eq true"},
            "backgroundColor": "rgba(153,27,27,0.4)", "color": "#fca5a5", "fontWeight": "bold",
        }],
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": "#161b22", "color": "#e6e6e6",
            "border": "1px solid #30363d", "textAlign": "left", "padding": "8px",
        },
    )

    updated_text = datetime.now().strftime("%I:%M:%S %p")
    status_msg   = "Connected"
    status_cls   = "text-sm font-medium px-3 py-1 rounded-full bg-green-900 text-green-300"

    return fig, panel_cls, icon, header_text, msg_text, table_out, updated_text, status_msg, status_cls

# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("[FIRO] 🚀  Starting FIRO dashboard — http://localhost:5000")
    print("[FIRO]     Analytics panel — http://localhost:5000/dash/")
    app.run(debug=True, host="0.0.0.0", port=5000)
