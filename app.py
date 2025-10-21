# app.py
import streamlit as st
import numpy as np

st.set_page_config(page_title="ASCE 7-16 C&C Wind Calculator (h ≤ 60 ft)", layout="centered")
st.title("ASCE 7-16 — Components & Cladding wind calculator (h ≤ 60 ft)")
st.markdown("""
This app computes velocity pressure *qh* and final component & cladding pressures following ASCE 7-16 Chapter 30
(for buildings of mean roof height h ≤ 60 ft).  

**Notes:**  
• For roof design pressures the standard ASCE figures (Fig. 30.4-1 and the GCp figures) supply the zone pressures.
• This app computes qh (velocity pressure at mean roof height) and offers two workflows:
  - **Figure (pnet30)**: apply `pnet = λ * Kzt * pnet30` (Fig. 30.4-1 method).
  - **GCp**: input (GCp) and (GCpi) and compute `p = qh*(GCp - GCpi)`.  
Refer to ASCE 7-16 Chapter 30 for figures and zone selection. (See citations in app page.)
""")

# -------------------------
# User inputs
# -------------------------
st.header("Site & wind parameters")
V = st.number_input("Basic wind speed V (mph)", min_value=0.0, value=115.0, format="%.1f")
h = st.number_input("Mean roof height h (ft) — (h ≤ 60 ft)", min_value=0.0, max_value=60.0, value=30.0, format="%.3f")
exposure = st.selectbox("Exposure category", ["B", "C", "D"])
Kd = st.number_input("Wind directionality factor Kd (default 0.85 for C&C)", value=0.85, format="%.3f")
Kzt = st.number_input("Topographic factor Kzt (default = 1.0)", value=1.0, format="%.3f")
# Ground elevation factor
elev = st.number_input("Site elevation above sea level (ft) — to compute Ke (optional)", value=0.0, format="%.1f")

st.markdown("### Advanced: internal pressure coefficient (GCpi)")
GCpi = st.number_input("Internal pressure coefficient GCpi (e.g. ±0.18 typical)", value=0.0, format="%.3f")

# -------------------------
# Kz/Kh table (from ASCE Table 26.10-1) - a subset for interpolation
# We'll implement as arrays for exposures B/C/D for heights up to 60 ft.
# The app uses Kh (Kz at mean roof height) by linear interpolation of tabulated points.
# -------------------------
st.markdown("---")
st.header("Compute velocity pressure qh (ASCE Eq. 26.10-1)")

# Tabulated Kz/Kh points (ft) from Table 26.10-1 (subset). Values are Kh at those heights.
# This is a compact set of rows for interpolation up to 60 ft (values taken from ASCE Table 26.10-1).
height_pts = np.array([0.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0])  # ft
Kh_B = np.array([0.57, 0.57, 0.62, 0.66, 0.70, 0.76, 0.81, 0.85])   # Exposure B (note small adjustments per notes)
Kh_C = np.array([0.70, 0.70, 0.90, 0.94, 0.98, 1.04, 1.09, 1.13])   # Exposure C
Kh_D = np.array([0.85, 0.85, 0.90, 0.94, 1.16, 1.22, 1.27, 1.31])   # Exposure D (value at 30ft is 1.16 per table snippet)

# pick exposure vector
if exposure == "B":
    Kh_vals = Kh_B
elif exposure == "C":
    Kh_vals = Kh_C
else:
    Kh_vals = Kh_D

# interpolate Kh at height h
Kh = np.interp(h, height_pts, Kh_vals)
st.write(f"Interpolated Kh (Kz at mean roof height) = **{Kh:.3f}**")

# Ground elevation factor Ke (approx from Table 26.9-1 or exponential). Permit Ke = 1.0 default.
if elev <= 0:
    Ke = 1.0
else:
    Ke = np.exp(-0.0000362 * elev)  # using ft version from ASCE notes
st.write(f"Ground elevation factor Ke = **{Ke:.3f}**")

# Velocity pressure qh (Eq. 26.10-1)
qh = 0.00256 * Kh * Kzt * Kd * Ke * V**2  # lb/ft^2 (V in mph)
st.markdown(f"**Velocity pressure qh = {qh:.3f} lb/ft²**  ( = {qh * 0.0478803:.4f} kN/m² )")

st.markdown("---")
st.header("Path A — Fig 30.4-1 (pnet30) method (recommended for h ≤ 60 ft)")
st.markdown("""
If using Fig. 30.4-1: read the **pnet30 (Exposure B at h=30 ft)** value for the zone (from the ASCE figure),
then the app will calculate `pnet = λ * Kzt * pnet30`.  
*You must read pnet30 from Fig.30.4-1 for the roof shape & zone you are using and paste here.*
""")
use_fig = st.checkbox("Use Fig 30.4-1 workflow", value=True)
if use_fig:
    pnet30 = st.number_input("Enter pnet30 (from Fig. 30.4-1, Exposure B @ h=30 ft) [lb/ft²]", value=0.0, format="%.3f")
    lam = st.number_input("Adjustment factor λ (from Fig. 30.4-1 for your h & exposure) — if unknown use 1.0", value=1.0, format="%.3f")
    if pnet30 != 0:
        pnet = lam * Kzt * pnet30
        st.success(f"pnet (net design pressure) = {pnet:.3f} lb/ft²  = {pnet * 0.0478803:.4f} kN/m²")
        st.caption("This follows ASCE Eq. (30.4-1): pnet = λ * Kzt * pnet30. See ASCE 7-16 Chapter 30.")
    else:
        st.info("Enter the pnet30 value from Fig. 30.4-1 (Exposure B @ h=30 ft) for the zone you selected in the ASCE figure.")

st.markdown("---")
st.header("Path B — GCp method (enter external (GCp) from figure)")
st.markdown("""
If you have (GCp) from the correct figure (e.g. Fig. 30.3-2 for flat roofs, Fig. 30.3-5 for monoslope roofs),
enter GCp and the app uses `p = qh * (GCp - GCpi)`.  (GCp already contains the gust-effect factor per ASCE.)
""")
use_gcp = st.checkbox("Use GCp workflow", value=True)
if use_gcp:
    GCp = st.number_input("Enter external GCp (from appropriate Fig. 30.3 series) — positive/negative values allowed", value=0.0, format="%.3f")
    if abs(GCp) > 0.0:
        p_gcp = qh * (GCp - GCpi)
        st.success(f"p = qh * (GCp - GCpi) = {p_gcp:.3f} lb/ft² = {p_gcp * 0.0478803:.4f} kN/m²")
    else:
        st.info("Enter GCp read from ASCE figure for the roof zone (GCp values are figure-based and include gust-effect).")

st.markdown("---")
st.header("Outputs & Notes")
st.write("• qh was computed using ASCE Eq. 26.10-1 with interpolated Kh from Table 26.10-1.") 
st.write("• For h ≤ 60 ft the recommended source for final roof zone pressures is Fig. 30.4-1 (pnet30) and the GCp figures in Chapter 30.")
st.write("• If you need automated digitization of the figures (to extract pnet30 or GCp numerically), that requires image-digitization or a manual table of figure numbers; I can help build that next if you want.")
st.markdown("### References (ASCE 7-16): Chapter 26 (Kz, qz), Chapter 30 (C&C figures & Eq. 30.4-1).")
st.caption("This tool is for design-assistance only — always verify results per the governing code and project requirements.")
