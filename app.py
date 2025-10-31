import streamlit as st
import plotly.graph_objects as go
import urllib.parse
import requests
import json

st.set_page_config(page_title="Wind Load Calculator", layout="centered")

st.title("🌪️ Wind Load Calculator (ASCE 7)")

st.markdown("""
This calculator helps you organize inputs for **ASCE 7 wind load determination**.  
It guides you to the [ASCE Hazard Tool](https://ascehazardtool.org/) for site-specific wind speeds  
and visualizes your building dimensions in 3D.
""")

st.markdown("---")

# -----------------------
# 1. BUILDING DIMENSIONS
# -----------------------
st.header("1️⃣ Building Dimensions")

col1, col2, col3 = st.columns(3)
with col1:
    least_width = st.number_input("Least Width (ft)", min_value=0.0, value=30.0, format="%.2f")
with col2:
    longest_width = st.number_input("Longest Width (ft)", min_value=0.0, value=80.0, format="%.2f")
with col3:
    height = st.number_input("Mean Roof Height (ft)", min_value=0.0, value=30.0, format="%.2f")

st.markdown(f"""
**Summary:**  
- Least Width (x): `{least_width} ft`  
- Longest Width (y): `{longest_width} ft`  
- Height (z): `{height} ft`
""")

# -----------------------
# 3D CUBE VISUALIZATION
# -----------------------
st.subheader("📦 Building Shape Visualization")

# Define cube vertices (rectangular prism)
x = [0, least_width, least_width, 0, 0, least_width, least_width, 0]
y = [0, 0, longest_width, longest_width, 0, 0, longest_width, longest_width]
z = [0, 0, 0, 0, height, height, height, height]

# Define faces via vertex indices
faces = [
    [0,1,2,3],  # bottom
    [4,5,6,7],  # top
    [0,1,5,4],  # front
    [2,3,7,6],  # back
    [1,2,6,5],  # right
    [0,3,7,4]   # left
]

fig = go.Figure()

# Draw each face
for f in faces:
    fig.add_trace(go.Mesh3d(
        x=[x[i] for i in f],
        y=[y[i] for i in f],
        z=[z[i] for i in f],
        color='lightblue',
        opacity=0.50,
        i=[0,1,2],
        j=[1,2,3],
        k=[2,3,0],
        flatshading=True,
        showscale=False
    ))

fig.update_layout(
    scene=dict(
        xaxis_title='Width (ft)',
        yaxis_title='Length (ft)',
        zaxis_title='Height (ft)',
        aspectmode='data',
        xaxis=dict(nticks=4, backgroundcolor="white"),
        yaxis=dict(nticks=4, backgroundcolor="white"),
        zaxis=dict(nticks=4, backgroundcolor="white"),
    ),
    width=600, height=500,
    margin=dict(r=10, l=10, b=10, t=10),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.header("2️⃣ Code Jurisdiction")
st.title("Building Code Edition Lookup")

# List of all U.S. states and D.C.
states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
    "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

st.title("Building Code Lookup by State")

state = st.selectbox("Select the project location (State):", states)

st.write(f"You selected: **{state}**")

if location_input:
    st.info("Select the project’s state (based on the location above):")
    state = st.selectbox("State:", states)

# location = st.text_input("📍 Enter Project Location (City, State or ZIP):", placeholder="e.g., Chicago, IL or 77002")

# # Placeholder function — you’ll need real API endpoint & key
# def lookup_icc_adoption(location_str, api_key):
#     # In a real implementation you'd parse the location into state/county,
#     # call the ICC “ImageCode Adoption Database” API with query parameters.
#     # Here is a dummy placeholder to illustrate.
#     try:
#         query = urllib.parse.quote(location_str)
#         url = f"https://api.iccsafe.org/adoption/v1/jurisdictions?search={query}&key={api_key}"
#         resp = requests.get(url, timeout=10)
#         if resp.status_code == 200:
#             data = resp.json()
#             if data and "items" in data and len(data["items"]) > 0:
#                 # assume first item
#                 adoption = data["items"][0]
#                 return {
#                     "jurisdiction": adoption.get("name"),
#                     "IBC": adoption.get("code_title"),
#                     "IBC_effective": adoption.get("effective_date"),
#                 }
#     except Exception as e:
#         st.error(f"Lookup failed: {e}")
#     return None

# api_key = st.text_input("Enter your ICC API Key (for automated lookup)", type="password")

# adoption_info = None
# if location and api_key:
#     with st.spinner("Attempting to lookup code adoption..."):
#         adoption_info = lookup_icc_adoption(location, api_key)

# if adoption_info:
#     st.success(f"Found jurisdiction: {adoption_info['jurisdiction']}")
#     st.write(f"Adopted IBC Edition: **{adoption_info['IBC']}** (effective {adoption_info['IBC_effective']})")
#     # As the ASCE version may not be in API, ask user manually:
#     asce_code = st.selectbox("Select applicable ASCE 7 Edition:", ["ASCE 7-10", "ASCE 7-16", "ASCE 7-22"])
# else:
#     st.info("Automatic lookup not successful. Please select code editions manually:")
#     ibc_code = st.selectbox("Select IBC Edition:", ["IBC 2015", "IBC 2018", "IBC 2021", "IBC 2024"])
#     asce_code = st.selectbox("Select applicable ASCE 7 Edition:", ["ASCE 7-10", "ASCE 7-16", "ASCE 7-22"])

# st.write(f"Using IBC: **{ibc_code if not adoption_info else adoption_info['IBC']}**, ASCE 7: **{asce_code}**")
# -----------------------
# 3. RISK CATEGORY
# -----------------------
st.header("3️⃣ Risk Category")

risk_map = {
    "I": "Low risk to human life (e.g., storage, barns).",
    "II": "Typical occupancy (residential, commercial, offices).",
    "III": "Substantial hazard to human life (schools, large assemblies).",
    "IV": "Essential facilities (hospitals, emergency services)."
}
risk_category = st.selectbox(
    "Select Risk Category:",
    list(risk_map.keys()),
    format_func=lambda x: f"Category {x} – {risk_map[x].split('(')[0]}"
)
st.info(risk_map[risk_category])

# -----------------------
# 4. WIND SPEED
# -----------------------
st.header("4️⃣ Wind Speed")

st.markdown("""
Get your project’s **basic wind speed (V)** from the official ASCE Hazard Tool:  
👉 [https://ascehazardtool.org/](https://ascehazardtool.org/)
""")

V = st.number_input("Enter Basic Wind Speed (mph):", min_value=0.0, value=115.0, format="%.1f")
st.success(f"Using V = {V:.1f} mph")

st.markdown("---")


# -----------------------
# SUMMARY OUTPUT
# -----------------------
st.markdown("---")
st.header("✅ Summary of Inputs")

st.markdown(f"""
| Parameter | Value |
|------------|--------|
| Least Width | {least_width} ft |
| Longest Width | {longest_width} ft |
| Mean Roof Height | {height} ft |
| ASCE Edition | {asce_code} |
| Risk Category | {risk_category} |
| Basic Wind Speed | {V:.1f} mph |
""")

st.markdown("""
You can now use these inputs for **ASCE 7 Chapter 30 (C&C)** or **Main Wind Force Resisting System** design.
""")

st.caption("Developed for educational use. Always verify results per ASCE 7 and local building code.")
