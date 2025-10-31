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
    Extracts building, IBC, ASCE 7, IECC, and ASHRAE codes from the raw text string.
    """
    building_code = ""
    ibc_code = ""
    asce_code = ""
    iecc_code = ""
    ashrae_code = ""

    # Simple pattern search (can refine later)
    if "Building" in code_text or "Code" in code_text:
        building_code = code_text
    if "IBC" in code_text:
        ibc_code = code_text
    if "ASCE" in code_text:
        asce_code = code_text
    if "IECC" in code_text:
        iecc_code = code_text
    if "ASHRAE" in code_text or "90.1" in code_text:
        ashrae_code = code_text

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

    st.subheader(f"📍 Building Code Summary for {selected_state}")
    st.write(f"**Raw Extracted Info:** {code_text}")
    st.markdown("---")

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
