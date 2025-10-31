import streamlit as st
import plotly.graph_objects as go
import requests
import json
#import tabula
import pandas as pd
import io

# ----------------------------------------------------
# Streamlit Page Setup
# ----------------------------------------------------
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
st.subheader("📦 Building Shape Visualization")

x = [0, least_width, least_width, 0, 0, least_width, least_width, 0]
y = [0, 0, longest_width, longest_width, 0, 0, longest_width, longest_width]
z = [0, 0, 0, 0, height, height, height, height]
faces = [
    [0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]
]

fig = go.Figure()
for f in faces:
    fig.add_trace(go.Mesh3d(
        x=[x[i] for i in f],
        y=[y[i] for i in f],
        z=[z[i] for i in f],
        color='lightblue', opacity=0.5, showscale=False
    ))

fig.update_layout(
    scene=dict(
        xaxis_title='Width (ft)', yaxis_title='Length (ft)', zaxis_title='Height (ft)',
        aspectmode='data',
        xaxis=dict(nticks=4, backgroundcolor="white"),
        yaxis=dict(nticks=4, backgroundcolor="white"),
        zaxis=dict(nticks=4, backgroundcolor="white"),
    ),
    width=600, height=500, margin=dict(r=10, l=10, b=10, t=10)
)
st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

# ----------------------------------------------------
# 2️⃣  Code Jurisdiction / Adoption Lookup
# ----------------------------------------------------
st.header("2️⃣ Code Jurisdiction Lookup")

states = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
    "District of Columbia","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas",
    "Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi",
    "Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
    "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
    "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington",
    "West Virginia","Wisconsin","Wyoming"
]
state_choice = st.selectbox("Select Project State:", states)

# ----------------------------------------------------
# Fetch ICC Adoption Chart and Parse
# ----------------------------------------------------
PDF_URL = "https://www.iccsafe.org/wp-content/uploads/Master-I-Code-Adoption-Chart-1.pdf"

@st.cache_data(show_spinner=False)
def load_icc_table():
    try:
        response = requests.get(PDF_URL, timeout=20)
        response.raise_for_status()
        tables = tabula.read_pdf(io.BytesIO(response.content), pages="all", multiple_tables=True)
        for t in tables:
            if "State" in t.columns:
                df = t.copy()
                df.columns = [str(c).strip() for c in df.columns]
                df = df.dropna(subset=["State"])
                df["State"] = df["State"].str.strip()
                cols = [c for c in df.columns if "IBC" in c or "IECC" in c or c == "State"]
                return df[cols]
    except Exception as e:
        st.error(f"PDF parse failed: {e}")
        return pd.DataFrame(columns=["State","IBC","IECC"])
    return pd.DataFrame(columns=["State","IBC","IECC"])

df_codes = load_icc_table()

if not df_codes.empty and state_choice in df_codes["State"].values:
    row = df_codes[df_codes["State"] == state_choice].iloc[0]
    ibc_val = next((row[c] for c in row.index if "IBC" in c), "N/A")
    iecc_val = next((row[c] for c in row.index if "IECC" in c), "N/A")

    st.success(f"**{state_choice} Adopted Codes:**")
    st.write(f"- 🏛️ Building Code (IBC): **{ibc_val}**")
    st.write(f"- 🌡️ Energy Code (IECC): **{iecc_val}**")

    # --- Derived Relationships ---
    if "2024" in str(ibc_val):
        asce = "ASCE 7-22"
    elif "2021" in str(ibc_val):
        asce = "ASCE 7-16"
    else:
        asce = "ASCE 7-10 or earlier"

    if "2021" in str(iecc_val):
        ashrae = "ASHRAE 90.1-2019"
    elif "2018" in str(iecc_val):
        ashrae = "ASHRAE 90.1-2016"
    else:
        ashrae = "ASHRAE 90.1-2013 or earlier"

    st.write(f"- 📘 Referenced ASCE 7 Edition: **{asce}**")
    st.write(f"- ⚙️ Referenced ASHRAE 90.1 Edition: **{ashrae}**")
else:
    st.warning("Selected state not found in parsed ICC table.")

st.markdown("---")

# # ----------------------------------------------------
# # 3️⃣  Risk Category
# # ----------------------------------------------------
# st.header("3️⃣ Risk Category")
# risk_map = {
#     "I": "Low risk to human life (e.g., storage, barns).",
#     "II": "Typical occupancy (residential, commercial, offices).",
#     "III": "Substantial hazard to human life (schools, assemblies).",
#     "IV": "Essential facilities (hospitals, emergency services)."
# }
# risk_category = st.selectbox("Select Risk Category:", list(risk_map.keys()),
#                              format_func=lambda x: f"Category {x} – {risk_map[x].split('(')[0]}")
# st.info(risk_map[risk_category])

# # ----------------------------------------------------
# # 4️⃣  Wind Speed
# # ----------------------------------------------------
# st.header("4️⃣ Wind Speed")
# st.markdown("Get site-specific wind speed from 👉 [ASCE Hazard Tool](https://ascehazardtool.org/)")
# V = st.number_input("Enter Basic Wind Speed (mph):", min_value=0.0, value=115.0, format="%.1f")
# st.success(f"Using V = {V:.1f} mph")
# st.markdown("---")

# # ----------------------------------------------------
# # ✅  Summary Output
# # ----------------------------------------------------
# st.header("✅ Summary of Inputs")

# summary_table = f"""
# | Parameter | Value |
# |------------|--------|
# | Least Width | {least_width} ft |
# | Longest Width | {longest_width} ft |
# | Mean Roof Height | {height} ft |
# | IBC Edition | {ibc_val if 'ibc_val' in locals() else 'N/A'} |
# | ASCE 7 Edition | {asce if 'asce' in locals() else 'N/A'} |
# | IECC Edition | {iecc_val if 'iecc_val' in locals() else 'N/A'} |
# | ASHRAE 90.1 | {ashrae if 'ashrae' in locals() else 'N/A'} |
# | Risk Category | {risk_category} |
# | Basic Wind Speed | {V:.1f} mph |
# """
# st.markdown(summary_table)
# st.caption("Developed for educational use. Always verify results per ASCE 7 and local code.")
