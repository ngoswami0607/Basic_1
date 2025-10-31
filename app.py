import streamlit as st
import requests
import plotly.graph_objects as go 
import pdfplumber
import pandas as pd
import io
import urllib.parse 
import json 
import openai 
import io
import re


st.set_page_config(page_title="Wind Load Calculator", layout="centered")

st.title("🌪️ Wind Load Calculator (ASCE 7)")

st.markdown("""
This calculator helps you organize inputs for **ASCE 7 wind load determination**.  
It guides you to the [ASCE Hazard Tool](https://ascehazardtool.org/) for site-specific wind speeds  
and visualizes your building dimensions in 3D.
""")
st.markdown("---")

# ----------------------------------------------------
# 1️⃣  Building Dimensions
# ----------------------------------------------------
st.header("1️⃣ Building Dimensions")

col1, col2, col3 = st.columns(3)
least_width = col1.number_input("Least Width (ft)", min_value=0.0, value=30.0, format="%.2f")
longest_width = col2.number_input("Longest Width (ft)", min_value=0.0, value=80.0, format="%.2f")
height = col3.number_input("Mean Roof Height (ft)", min_value=0.0, value=30.0, format="%.2f")

st.markdown(f"""
**Summary:**  
- Least Width (x): `{least_width} ft`  
- Longest Width (y): `{longest_width} ft`  
- Height (z): `{height} ft`
""")

# ----------------------------------------------------
# 3D CUBE VISUALIZATION
# ----------------------------------------------------
# Convert to ft-in string
def ft_in(value):
    ft = int(value)
    inches = round((value - ft) * 12)
    return f"{ft}′-{inches}″"

st.subheader("📦 Building Shape Visualization")

# 8 cube vertices
x = [0, least_width, least_width, 0, 0, least_width, least_width, 0]
y = [0, 0, longest_width, longest_width, 0, 0, longest_width, longest_width]
z = [0, 0, 0, 0, height, height, height, height]

# Triangular faces of the cuboid
i = [0, 0, 0, 1, 1, 2, 3, 4, 4, 5, 6, 7]
j = [1, 2, 3, 2, 5, 3, 7, 5, 6, 6, 7, 4]
k = [5, 3, 4, 5, 6, 7, 4, 6, 7, 4, 4, 5]

# Create the 3D cube mesh
fig = go.Figure(data=[
    go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color='lightblue',
        opacity=1.0,
        flatshading=True,
        name='Building',
        showlegend=False
    )
])

# Add wireframe edges (hidden from legend)
edges = [
    (0,1), (1,2), (2,3), (3,0),  # bottom
    (4,5), (5,6), (6,7), (7,4),  # top
    (0,4), (1,5), (2,6), (3,7)   # verticals
]
for e in edges:
    fig.add_trace(go.Scatter3d(
        x=[x[e[0]], x[e[1]]],
        y=[y[e[0]], y[e[1]]],
        z=[z[e[0]], z[e[1]]],
        mode='lines',
        line=dict(color='black', width=4),
        showlegend=False
    ))

# Add 3D dimension labels
fig.add_trace(go.Scatter3d(
    x=[least_width/2], y=[-5], z=[0],
    mode='text',
    text=[f"Width: {ft_in(least_width)}"],
    textposition="bottom center",
    showlegend=False
))
fig.add_trace(go.Scatter3d(
    x=[-5], y=[longest_width/2], z=[0],
    mode='text',
    text=[f"Length: {ft_in(longest_width)}"],
    textposition="bottom center",
    showlegend=False
))
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[height + 5],
    mode='text',
    text=[f"Height: {ft_in(height)}"],
    textposition="top center",
    showlegend=False
))

# Layout cleanup
fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        zaxis=dict(visible=False),
        aspectmode='data'
    ),
    paper_bgcolor="white",
    margin=dict(r=10, l=10, b=10, t=10),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("---")


# ----------------------------------------------------
# 2️⃣  Code Jurisdiction / Adoption Lookup
# ----------------------------------------------------
st.header("2️⃣ Code Jurisdiction Lookup")

# --- Function to extract ICC adoption data directly from the PDF ---
@st.cache_data(show_spinner=True)
def load_icc_table_pdfplumber():
    PDF_URL = "https://www.iccsafe.org/wp-content/uploads/Master-I-Code-Adoption-Chart-1.pdf"
    response = requests.get(PDF_URL)
    response.raise_for_status()

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Extract lines that look like state rows
    states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
        "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana",
        "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts",
        "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska",
        "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
        "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
        "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
        "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ]

    states_data = []
    lines = text.split("\n")
    current_state = None
    buffer = ""

    for line in lines:
        # If a line starts with a state name, start a new entry
        if any(line.startswith(s) for s in states):
            if current_state and buffer.strip():
                states_data.append([current_state, buffer.strip()])
            current_state = line.split(" ")[0]
            buffer = line[len(current_state):].strip()
        else:
            buffer += " " + line.strip()

    if current_state and buffer.strip():
        states_data.append([current_state, buffer.strip()])

    df = pd.DataFrame(states_data, columns=["State", "Code Info"])
    return df


# --- Helper Function: Extract Relevant Codes ---
def extract_relevant_codes(code_text):
    """
    Extract building, IBC, ASCE 7, IECC, and ASHRAE codes from the text.
    Works with both keyword-based and compressed numeric-only formats.
    """
    # Normalize
    text = code_text.upper().replace("–", "-").replace("—", "-")

    # Initialize
    building_code = ibc_code = asce_code = iecc_code = ashrae_code = ""

    # --- 1️⃣ Try to extract by keywords ---
    ibc_match = re.search(r"IBC\s*(19|20)\d{2}", text)
    asce_match = re.search(r"ASCE\s*7[-–]\s*(\d{2})", text)
    iecc_match = re.search(r"IECC\s*(19|20)\d{2}", text)
    ashrae_match = re.search(r"(ASHRAE|90\.1)[-\s]*(19|20)\d{2}", text)

    if ibc_match:
        ibc_code = f"IBC {ibc_match.group(0).split()[-1]}"
    if asce_match:
        asce_code = f"ASCE 7-{asce_match.group(1)}"
    if iecc_match:
        iecc_code = f"IECC {iecc_match.group(0).split()[-1]}"
    if ashrae_match:
        ashrae_code = f"ASHRAE 90.1-{ashrae_match.group(2)}"
    if ibc_code:
        building_code = ibc_code

    # --- 2️⃣ Fallback: numeric compressed form like “15 X 15 09 15 15” ---
    if not any([ibc_code, asce_code, iecc_code, ashrae_code]):
        years = re.findall(r'\b(0[9]|1[0-9]|2[0-5])\b', text)
        if len(years) >= 1:
            ibc_code = f"IBC 20{years[0]}"
            building_code = f"Building Code 20{years[0]}"
        if len(years) >= 2:
            asce_code = f"ASCE 7-20{years[1]}"
        if len(years) >= 3:
            iecc_code = f"IECC 20{years[2]}"
        if len(years) >= 4:
            ashrae_code = f"ASHRAE 90.1-20{years[3]}"

    return building_code, ibc_code, asce_code, iecc_code, ashrae_code

# --- Streamlit App ---
st.title("US State Building Code Finder 🏗️")
st.markdown("This app retrieves the latest **ICC Building Code adoption data** directly from the official ICC PDF and extracts key information for each U.S. state.")

# Load PDF and parse data
with st.spinner("Loading ICC adoption data..."):
    df_codes = load_icc_table_pdfplumber()

# Dropdown for selecting a state
state_list = sorted(df_codes["State"].unique())
selected_state = st.selectbox("Select a U.S. State:", state_list)

# Find selected state info
state_info = df_codes[df_codes["State"] == selected_state]
if not state_info.empty:
    code_text = state_info.iloc[0]["Code Info"]
    building_code, ibc_code, asce_code, iecc_code, ashrae_code = extract_relevant_codes(code_text)

    # st.subheader(f"📍 Building Code Summary for {selected_state}")
    # st.write(f"**Raw Extracted Info:** {code_text}")
    # st.markdown("---")

    st.markdown("### 🔍 Parsed Code References")
    st.write(f"**Building Code:** {building_code or 'N/A'}")
    st.write(f"**IBC Reference:** {ibc_code or 'N/A'}")
    st.write(f"**ASCE 7 Edition:** {asce_code or 'N/A'}")
    st.write(f"**IECC Edition:** {iecc_code or 'N/A'}")
    st.write(f"**ASHRAE 90.1 Edition:** {ashrae_code or 'N/A'}")

else:
    st.warning("State not found in the current ICC adoption dataset.")

st.markdown("---")
st.caption("Data Source: [ICC Master I-Code Adoption Chart](https://www.iccsafe.org/wp-content/uploads/Master-I-Code-Adoption-Chart-1.pdf)")

# ----------------------- 
# 3. RISK CATEGORY 
# ----------------------- 
st.header("3️⃣ Risk Category") 
risk_map = { "I": "Low risk to human life (e.g., storage, barns).", "II": "Typical occupancy (residential, commercial, offices).", "III": "Substantial hazard to human life (schools, large assemblies).", "IV": "Essential facilities (hospitals, emergency services)." } 
risk_category = st.selectbox( "Select Risk Category:", list(risk_map.keys()), format_func=lambda x: f"Category {x} – {risk_map[x].split('(')[0]}" ) 
st.info(risk_map[risk_category]) 

# ----------------------- 
# 4. WIND SPEED 
# ----------------------- 
st.header("4️⃣ Wind Speed") 
st.markdown(""" Get your project’s **basic wind speed (V)** from the official ASCE Hazard Tool: 👉 [https://ascehazardtool.org/](https://ascehazardtool.org/) """) 
V = st.number_input("Enter Basic Wind Speed (mph):", min_value=0.0, value=115.0, format="%.1f") 
st.success(f"Using V = {V:.1f} mph") 
st.markdown("---") 

# ----------------------------------------------------
# 5️⃣ BASIC WIND PRESSURE CALCULATION (ASCE 7)
# ----------------------------------------------------
st.header("5️⃣ Basic Wind Pressure Calculation (ASCE 7)")

# --- Select Structure Type for Kd ---
st.subheader("Select Structure Type (for Kd)")
structure_types = {
    "Main Wind Force Resisting System (Buildings)": 0.85,
    "Components and Cladding": 0.85,
    "Arched Roofs": 0.85,
    "Circular Domes": 1.0,
    "Chimneys / Tanks (Square)": 0.90,
    "Chimneys / Tanks (Hexagonal)": 0.95,
    "Chimneys / Tanks (Octagonal)": 1.0,
    "Chimneys / Tanks (Round)": 1.0,
    "Solid Freestanding Walls or Signs": 0.85,
    "Open Signs / Single-Plane Frames": 0.85,
    "Trussed Tower (Triangular / Rectangular)": 0.85,
    "Trussed Tower (Other Cross Sections)": 0.95
}
structure_selection = st.selectbox("Choose structure type:", list(structure_types.keys()))
Kd = structure_types[structure_selection]
st.info(f"**Selected Kd = {Kd:.2f}**")

# --- Surface Roughness / Exposure Category ---
st.subheader("Select Exposure Category (Surface Roughness)")
exposure_options = ["B", "C", "D"]
exposure = st.selectbox("Exposure Category:", exposure_options, index=1)
st.caption("Exposure B = urban/suburban, C = open terrain, D = flat/coastal areas")

# --- Compute Kz from Table 26.10-1 ---
def get_kz(height_ft, exposure):
    # Table 26.10-1 (ASCE 7-16)
    table = {
        "B": {15: 0.57, 20: 0.62, 25: 0.66, 30: 0.70, 40: 0.76, 50: 0.81, 60: 0.85, 70: 0.89, 80: 0.93, 90: 0.96, 100: 0.99, 120: 1.04, 140: 1.09, 160: 1.13, 200: 1.20, 250: 1.28, 300: 1.35, 350: 1.41, 400: 1.47, 450: 1.52, 500: 1.56},
        "C": {15: 0.85, 20: 0.90, 25: 0.94, 30: 0.98, 40: 1.04, 50: 1.09, 60: 1.13, 70: 1.17, 80: 1.21, 90: 1.24, 100: 1.26, 120: 1.31, 140: 1.36, 160: 1.39, 200: 1.46, 250: 1.53, 300: 1.59, 350: 1.64, 400: 1.69, 450: 1.73, 500: 1.77},
        "D": {15: 1.03, 20: 1.08, 25: 1.12, 30: 1.16, 40: 1.22, 50: 1.27, 60: 1.31, 70: 1.34, 80: 1.38, 90: 1.40, 100: 1.43, 120: 1.48, 140: 1.52, 160: 1.55, 200: 1.61, 250: 1.68, 300: 1.73, 350: 1.78, 400: 1.82, 450: 1.86, 500: 1.89}
    }

    h = min(max(height_ft, 15), 500)
    heights = sorted(table[exposure].keys())

    # Linear interpolation
    for i in range(len(heights)-1):
        h1, h2 = heights[i], heights[i+1]
        if h1 <= h <= h2:
            k1, k2 = table[exposure][h1], table[exposure][h2]
            return k1 + (k2 - k1) * ((h - h1) / (h2 - h1))
    return table[exposure][500]

Kz = get_kz(height, exposure)
st.success(f"Kz (at {height:.1f} ft, Exposure {exposure}) = **{Kz:.3f}**")

# --- Constants ---
Kzt = 1.0
Ke = 1.0

# --- Wind Pressure Calculation ---
q = 0.00256 * Kz * Kzt * Kd * Ke * (V ** 2)

st.markdown("### 💨 Calculated Velocity Pressure")
st.metric(label="q (psf)", value=f"{q:.2f}")

# --- Output breakdown ---
st.markdown(f"""
| Factor | Symbol | Value | Description |
|:--------|:--------|:--------|:-------------|
| Velocity Pressure Exposure Coefficient | Kz | {Kz:.3f} | Based on height and exposure |
| Topographic Factor | Kzt | {Kzt:.2f} | Default per ASCE 7-16 |
| Directionality Factor | Kd | {Kd:.2f} | From Table 26.6-1 |
| Ground Elevation Factor | Ke | {Ke:.2f} | Default |
| Basic Wind Speed | V | {V:.1f} mph | From ASCE Hazard Tool |
| **Velocity Pressure** | **q** | **{q:.2f} psf** | — |
""")
