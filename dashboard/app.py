import os
import json
import time
from datetime import datetime
# We try to import google.cloud, but we must handle the case where credentials fail later
try:
    from google.cloud import firestore
    # Import firestore types for querying (Query and FieldFilter for modern filtering)
    from google.cloud.firestore import Query, FieldFilter
except ImportError:
    # If running locally without the google-cloud-firestore package installed, 
    # this will be None, and the application will gracefully handle the missing DB connection.
    firestore = None 
    # Define dummy classes if import fails, so the code that uses them doesn't crash on definition
    class Query:
        DESCENDING = 'DESCENDING'
    class FieldFilter:
        def __init__(self, *args, **kwargs): pass

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output

# --- FALLBACK CONFIGURATION (Used if environment variables are missing) ---
LOCAL_PROJECT_ID = 'wildfire-monitoring-1ccca'
LOCAL_APP_ID = 'wildfire-monitoring-1ccca'


# --- 1. FIRESTORE INITIALIZATION ---

# Global variables provided by the Canvas environment (preferred) or fallbacks
APP_ID = os.environ.get('__app_id', LOCAL_APP_ID)
FIREBASE_CONFIG_JSON = os.environ.get('__firebase_config', '{}')

FIRESTORE_COLLECTION_NAME = "fire_logs" 
POLLING_INTERVAL_MS = 5000 

db = None # Initialize db to None
GCP_KEY_PATH = os.environ.get("GCP_KEY_PATH")

# Attempt to initialize Firestore Client
if firestore:
    try:
        firebase_config = json.loads(FIREBASE_CONFIG_JSON)
        # Use project ID from environment/config, or the local fallback
        project_id = firebase_config.get('projectId', LOCAL_PROJECT_ID)

        # Priority 1: Use explicit service account key (for specialized local testing)
        if GCP_KEY_PATH and os.path.exists(GCP_KEY_PATH):
            db = firestore.Client.from_service_account_json(GCP_KEY_PATH, project=project_id)
            print("Firestore Client Initialized using Service Account Key.")
        
        # Priority 2: Use Application Default Credentials (ADC) or Implicit Credentials
        elif project_id:
            db = firestore.Client(project=project_id)
            print("Firestore Client Initialized using Application Default Credentials (ADC).")

        if not db:
            raise Exception("No valid credentials found or project ID unavailable.")

    except Exception as e:
        # Fallback if config is missing or invalid, or credentials fail
        print(f"Warning: Could not initialize Firestore Client: {e}")
        print("The app will run but will not display real-time data until authentication is fixed.")


# --- 2. DATA FETCHING FUNCTION ---

def get_latest_fire_data():
    """Fetches the latest 50 fire logs from Firestore, filtered to the last 1 hour."""
    
    # Required columns for the internal application logic (using clean mapping names)
    REQUIRED_COLUMNS = ['timestamp', 'timestamp_str', 'coords_x', 'coords_y', 
                        'fire_probability', 'cameraLocation', 'severity']
                        
    if not db:
        return pd.DataFrame(columns=REQUIRED_COLUMNS) 

    # Construct the full public collection path
    collection_path = f"artifacts/{APP_ID}/public/data/{FIRESTORE_COLLECTION_NAME}"
    
    try:
        # Calculate timestamp for one hour ago (in ms)
        # We fetch data only from the last 60 minutes
        one_hour_ago_ms = int(time.time() * 1000) - (60 * 60 * 1000)

        # Query the collection: FILTERED to last 1 hour, ordered by timestamp (most recent first)
        # FIX: Using FieldFilter with the 'filter' keyword argument to remove the UserWarning.
        query = db.collection(collection_path).where(
            filter=FieldFilter('timestamp_ms', '>=', one_hour_ago_ms)
        ).order_by(
            'timestamp_ms', direction=Query.DESCENDING
        ).limit(50) # Limit to 50 most recent documents from the last hour
        
        docs = query.stream()
        
        data = []
        for doc in docs:
            log = doc.to_dict()
            
            # --- Field Mapping & Data Cleaning ---
            processed_log = {}
            try:
                # Map and convert types defensively
                processed_log['timestamp'] = log.get('timestamp_ms', int(time.time()*1000))
                
                # If timestamp_str is missing, generate one from the ms timestamp
                if 'timestamp_str' not in log:
                    ts_ms = processed_log['timestamp']
                    processed_log['timestamp_str'] = datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    processed_log['timestamp_str'] = log.get('timestamp_str')

                processed_log['coords_x'] = float(log.get('coords_x', 0))
                processed_log['coords_y'] = float(log.get('coords_y', 0))
                processed_log['fire_probability'] = float(log.get('fire_probability', 0))
                
                # Apply the requested field renames for cleaner app usage:
                processed_log['cameraLocation'] = log.get('camera_location', 'Unknown')
                processed_log['severity'] = log.get('detection_class', 'N/A') 
                
            except ValueError:
                # Skip logs with bad data
                continue
            data.append(processed_log)
            
        df = pd.DataFrame(data)
        
        if df.empty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS) 

        # Find the single latest log for each unique camera location for map markers
        latest_logs = df.sort_values('timestamp', ascending=False).drop_duplicates(subset=['cameraLocation'])
        
        return latest_logs
        
    except Exception as e:
        print(f"Error fetching data from Firestore: {e}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

# --- 3. DASH APPLICATION LAYOUT ---

# Define the fire detection threshold
FIRE_THRESHOLD = 0.70

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=['https://unpkg.com/tailwindcss@2.2.19/dist/tailwind.min.css'])

# Dark Mode Colors for Plotly (Matches HTML theme)
PLOTLY_DARK_THEME = {
    'bgcolor': '#161b22',
    'paper_bgcolor': '#161b22',
    'plot_bgcolor': '#161b22',
    'font': {'color': '#e6e6e6'},
    'mapbox_style': 'carto-darkmatter' # Dark Map Style
}

app.layout = html.Div(className='p-6 min-h-screen bg-gray-900 text-white font-sans', children=[
    
    # Hidden interval component to trigger updates
    dcc.Interval(
        id='interval-component',
        interval=POLLING_INTERVAL_MS, # in milliseconds
        n_intervals=0
    ),
    
    # Header
    html.Div(className='flex justify-between items-center pb-4 border-b border-gray-700 mb-4', children=[
        html.H1("Fire Monitor Dashboard (Python/Dash) - Last Hour Data", className='text-3xl font-bold text-cyan-400 tracking-wider'),
        html.Div(className='flex items-center space-x-4', children=[
            # Status badge (dynamically updated)
            html.Span(id='connection-status', className='text-sm font-medium px-3 py-1 rounded-full bg-green-900 text-green-300'),
            html.P(id='last-updated-time', className='text-sm text-gray-400'),
        ])
    ]),
    
    # Main Content Grid (Map and Data Panels)
    html.Div(className='grid grid-cols-1 lg:grid-cols-3 gap-6 h-full', style={'minHeight': '80vh'}, children=[
        
        # Map Panel (Col 1-2)
        html.Div(className='lg:col-span-2 rounded-xl bg-gray-800 shadow-xl p-0 overflow-hidden', children=[
            html.Div(className='h-full w-full', children=[
                dcc.Graph(
                    id='fire-map', 
                    config={'displayModeBar': False},
                    style={'height': '100%'}
                )
            ])
        ]),

        # Data Panel (Col 3)
        html.Div(className='lg:col-span-1 flex flex-col space-y-6 overflow-y-auto', children=[
            
            # Large Alert Panel
            html.Div(id='alert-panel', className='p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-gray-800', children=[
                html.Div(id='alert-icon-container', className='text-white mb-2'),
                html.H2(id='alert-header', className='text-3xl font-extrabold tracking-tight text-white mb-1'),
                html.P(id='alert-message', className='text-sm text-gray-400'),
            ]),
            
            # Recent History Table
            html.Div(className='flex-grow flex flex-col rounded-xl bg-gray-800 shadow-xl p-6 overflow-y-auto', children=[
                html.H3("RECENT LOG HISTORY (Last 60 Mins)", className='text-xl font-semibold mb-3 text-cyan-400 border-b border-gray-700 pb-2'),
                html.Div(id='log-table-container', className='overflow-y-auto flex-grow')
            ])
        ])
    ])
])

# --- 4. DASH CALLBACKS (DATA PROCESSING AND UI UPDATES) ---

@app.callback(
    [Output('fire-map', 'figure'),
     Output('alert-panel', 'className'),
     Output('alert-icon-container', 'children'),
     Output('alert-header', 'children'),
     Output('alert-message', 'children'),
     Output('log-table-container', 'children'),
     Output('last-updated-time', 'children'),
     Output('connection-status', 'children'),
     Output('connection-status', 'className'),
     ],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Callback triggered by the interval to fetch data and update all components."""
    
    df_latest = get_latest_fire_data()
    
    # Initialize return values for status indicators
    status_msg = "Data Fetching..."
    status_class = 'text-sm font-medium px-3 py-1 rounded-full bg-yellow-900 text-yellow-300'
    last_updated_text = "N/A"
    
    # Default UI states (All Clear / No Data)
    alert_panel_class = 'p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-gray-800'
    # Simple SVG for 'All Clear' status
    alert_icon = html.Div(html.Svg([html.Circle(cx="12", cy="12", r="10")], className='w-16 h-16 text-green-500', viewBox="0 0 24 24", fill="none", stroke="currentColor", strokeWidth="2", strokeLinecap="round", strokeLinejoin="round"))
    alert_header_text = 'ALL SYSTEMS GREEN'
    alert_message_text = 'No immediate fire threat detected in monitoring locations in the last hour.'
    table_content = html.P("No recent data found in the last 60 minutes.", className="text-center py-4 text-gray-500 text-sm")
    
    # Default map figure (centered on a generic location if no data is available yet)
    fig = go.Figure(layout=go.Layout(
        **PLOTLY_DARK_THEME,
        height=700,
        map_style='carto-darkmatter',
        mapbox=dict(center=dict(lat=34.0522, lon=-118.2437), zoom=8)
    ))
    
    # Check if data fetching was unsuccessful or returned an empty DataFrame
    if df_latest.empty:
        status_msg = "No Data"
        status_class = 'text-sm font-medium px-3 py-1 rounded-full bg-yellow-900 text-yellow-300'
        
        if not db:
            status_msg = "DB Disconnected"
            status_class = 'text-sm font-medium px-3 py-1 rounded-full bg-red-900/50 text-red-300'
            alert_header_text = 'DB CONNECTION FAILED'
            alert_message_text = 'Check Application Default Credentials (ADC) or deployment settings.'

        return (fig, alert_panel_class, alert_icon, alert_header_text, alert_message_text, table_content, last_updated_text, status_msg, status_class)

    # --- Data Processing ---
    
    df_latest['fire_probability'] = pd.to_numeric(df_latest['fire_probability'], errors='coerce').fillna(0)
    df_latest['is_fire'] = df_latest['fire_probability'] >= FIRE_THRESHOLD
    
    # 2. Find the row with max probability
    if not df_latest.empty and df_latest['fire_probability'].max() > 0:
        max_prob_row = df_latest.loc[df_latest['fire_probability'].idxmax()]
    else:
        max_prob_row = df_latest.iloc[0]

    # --- Map Update ---
    
    df_latest['color'] = df_latest['is_fire'].apply(lambda x: 'red' if x else 'green')
    df_latest['size'] = df_latest['fire_probability'].apply(lambda x: max(10, x * 30))

    fig = px.scatter_mapbox(df_latest, lat="coords_x", lon="coords_y", 
                            hover_name="cameraLocation", # Uses mapped name
                            hover_data={"fire_probability": ':.2f', "severity": True, "coords_x": False, "coords_y": False}, # Uses mapped name
                            color="color",
                            color_discrete_map={"red": "red", "green": "lime"},
                            size="size",
                            size_max=30,
                            zoom=8,
                            center={"lat": df_latest['coords_x'].mean(), "lon": df_latest['coords_y'].mean()}
                            )
    
    fig.update_layout(
        **PLOTLY_DARK_THEME,
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox_accesstoken=os.environ.get('MAPBOX_ACCESS_TOKEN', 'YOUR_MAPBOX_TOKEN_HERE'),
    )
    fig.update_traces(marker=dict(opacity=0.8, symbol='circle'))

    # --- Alert Panel Update ---
    if max_prob_row['is_fire']:
        prob_text = f"{(max_prob_row['fire_probability'] * 100):.2f}%"
        alert_panel_class = 'p-6 rounded-xl shadow-xl flex flex-col justify-center items-center flex-shrink-0 bg-red-900/50 animate-pulse'
        alert_header_text = '!!! CRITICAL FIRE ALERT !!!'
        alert_message_text = html.Span([
            f"HIGH RISK DETECTED at {max_prob_row.get('cameraLocation', 'Unknown Location')} with ",
            html.Strong(prob_text, className='text-red-400 font-bold'),
            " probability. Detection Class: ",
            html.Strong(max_prob_row.get('severity', 'N/A')) # Uses mapped name
        ])
        alert_icon = html.Div(html.Svg([html.Polygon(points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2")], 
                             className='w-16 h-16 text-red-500', viewBox="0 0 24 24", fill="none", stroke="currentColor", strokeWidth="2", strokeLinecap="round", strokeLinejoin="round"))
    
    # --- Log Table Update ---
    df_table = df_latest.head(5)[['timestamp_str', 'cameraLocation', 'fire_probability', 'is_fire']]
    
    table_content = dash_table.DataTable(
        id='log-table',
        columns=[
            {"name": "Time", "id": "timestamp_str", "type": "text"},
            {"name": "Location", "id": "cameraLocation", "type": "text"},
            {"name": "Prob.", "id": "fire_probability", "type": "numeric", "format": dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.percentage)},
        ],
        data=df_table.to_dict('records'),
        style_header={
            'backgroundColor': '#30363d',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{is_fire} eq true'},
                'backgroundColor': 'rgba(153, 27, 27, 0.4)',
                'color': '#fca5a5',
                'fontWeight': 'bold'
            }
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': '#161b22',
            'color': '#e6e6e6',
            'border': '1px solid #30363d',
            'textAlign': 'left',
            'padding': '8px'
        },
        hidden_columns=['is_fire'], 
    )
    
    # --- Status Update ---
    last_updated_text = datetime.now().strftime("%I:%M:%S %p")
    status_msg = 'Connected'
    status_class = 'text-sm font-medium px-3 py-1 rounded-full bg-green-900 text-green-300'
    
    return (fig, alert_panel_class, alert_icon, alert_header_text, alert_message_text, table_content, last_updated_text, status_msg, status_class)

# This line is crucial for Gunicorn/production servers
server = app.server

if __name__ == '__main__':
    print("Dash app starting on http://127.0.0.1:8050/")
    # If running locally, ensure you have the necessary Dash libraries installed:
    # pip install pandas dash plotly google-cloud-firestore
    app.run(debug=True)
