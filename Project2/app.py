import pandas as pd
import plotly.express as px
from plotly.colors import sample_colorscale
import plotly.express as px
from dash import ctx, Dash, dcc, html, Input, Output, State
from pycountry import countries

# Load merged GDP and GSP data
df = pd.read_csv("combined_gdp_gsp.csv")
df.loc[df["Type"] == "State", "GDP"] *= 1_000_000  # Multiply state values to match Country values


# Create a brighter version of Viridis (reduce blue)
brighter_viridis = sample_colorscale("Viridis", [0.3 + i * 0.1 for i in range(5)])  # 0.6 to 1.0

# State codes
state_abbrevs = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
}

# Fixes for country names not found by pycountry
manual_iso3 = {
    "Bahamas, The": "BHS", "Congo, Dem. Rep.": "COD", "Congo, Rep.": "COG",
    "Cote d'Ivoire": "CIV", "Egypt, Arab Rep.": "EGY", "Gambia, The": "GMB",
    "Hong Kong SAR, China": "HKG", "Iran, Islamic Rep.": "IRN",
    "Korea, Rep.": "KOR", "Korea, Dem. People's Rep.": "PRK", "Lao PDR": "LAO",
    "Macao SAR, China": "MAC", "Micronesia, Fed. Sts.": "FSM", "St. Kitts and Nevis": "KNA",
    "St. Lucia": "LCA", "St. Vincent and the Grenadines": "VCT", "Turkiye": "TUR",
    "Venezuela, RB": "VEN", "Vietnam": "VNM", "Yemen, Rep.": "YEM",
    "Kosovo": "XKX", "West Bank and Gaza": "PSE", "Curacao": "CUW",
    "Virgin Islands (U.S.)": "VIR"
}

def get_iso3(name):
    try:
        return countries.lookup(name).alpha_3
    except LookupError:
        return manual_iso3.get(name)

# Add location codes
df["state_code"] = df.apply(lambda row: state_abbrevs.get(row["Name"]) if row["Type"] == "State" else None, axis=1)
df["country_code"] = df.apply(lambda row: get_iso3(row["Name"]) if row["Type"] == "Country" else None, axis=1)
df["code"] = df["state_code"].combine_first(df["country_code"])

# App init
app = Dash(__name__)
latest_year = df[(df["Type"] == "Country") & (df["code"].notnull())]["Year"].max()

app.layout = html.Div(
    style={
        "backgroundColor": "#1E1E3F",  # dark blue
        "color": "white",              # light text for contrast
        "minHeight": "100vh",          # full page height
        "padding": "2rem"
    },
    children=[
        html.H2("GDP / GSP Comparison (1997–2024)"),
        dcc.Graph(id="gdp-line-chart"),
        html.Div([
            dcc.Graph(id="world-map", style={"display": "inline-block", "width": "48%"}),
            dcc.Graph(id="usa-map", style={"display": "inline-block", "width": "48%"})
        ]),
        dcc.Store(id="selected-locations", data=[])
    ]
)

# Selection logic
@app.callback(
    Output("selected-locations", "data"),
    Input("world-map", "clickData"),
    Input("usa-map", "clickData"),
    State("selected-locations", "data")
)

def queue_selection(world_click, usa_click, selected):
  # Determine which map was clicked
  triggered = ctx.triggered_id
  clickData = world_click if triggered == "world-map" else usa_click

  if not clickData:
      return selected

  code = clickData["points"][0]["location"]
  match = df[df["code"] == code]
  if match.empty:
      return selected
  name = match.iloc[0]["Name"]

  if not selected:
      return [name]
  if name == selected[-1]:
      return selected
  return [selected[-1], name] if len(selected) == 2 else selected + [name]

# Line chart
@app.callback(
    Output("gdp-line-chart", "figure"),
    Input("selected-locations", "data")
)

def update_line(locations):
    if not locations:
        return px.line(title="Click a location to begin comparison")

    recent = locations[-2:] if len(locations) >= 2 else locations
    filtered = df[df["Name"].isin(recent)]

    # Get a subset of Viridis colors (evenly spaced)
    colors = sample_colorscale("Viridis", [0.2, 0.8])[:len(recent)]

    # Manually build figure with color styling
    fig = px.line(
        filtered,
        x="Year",
        y="GDP",
        color="Name",
        title=" vs ".join(recent)
    )
    fig.update_layout(
    paper_bgcolor="#1F1F2E",
    plot_bgcolor="#1F1F2E",
    font_color="white")

    colors = sample_colorscale("Viridis", [0.8, 0.99])  # Brighter portion
    # Apply Viridis colors manually
    for i, trace in enumerate(fig.data):
        trace.update(line=dict(color=colors[i]), marker=dict(color=colors[i]))

    fig.update_traces(mode="lines+markers")
    return fig


# Map rendering
@app.callback(
    Output("world-map", "figure"),
    Output("usa-map", "figure"),
    Input("gdp-line-chart", "id")  
)
def render_maps(_):
    world_df = df[(df["Year"] == latest_year) & (df["Type"] == "Country")]
    us_df = df[(df["Year"] == latest_year) & (df["Type"] == "State")]

    world_fig = px.choropleth(
        world_df,
        locations="code",
        locationmode="ISO-3",
        color="GDP",
        hover_name="Name",
        title=f"World GDP",
        color_continuous_scale="Viridis",
        range_color=[0, 30_000_000_000_000]) 

    usa_fig = px.choropleth(
        us_df,
        locations="code",
        locationmode="USA-states",
        color="GDP",
        hover_name="Name",
        scope="usa",
        title=f"U.S. GSP",
        color_continuous_scale="Viridis",
        range_color=[0, 30_000_000_000_000])

    world_fig.update_layout(clickmode="event")
    usa_fig.update_layout(clickmode="event")

    return world_fig, usa_fig

# Run
if __name__ == "__main__":
    app.run(debug=True)
