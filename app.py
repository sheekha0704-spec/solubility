import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing & Sizing")
    
    # Input Area
    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            drug_input = st.text_input("Identify Target Drug", placeholder="e.g. Ibuprofen")
        with col2:
            st.write("##") # Alignment spacer
            if st.button("Perform AI Simulation", use_container_width=True):
                if drug_input:
                    with st.spinner("Processing chemical fingerprint..."):
                        props = fetch_drug_data(drug_input)
                        st.session_state.drug = drug_input
                        st.session_state.props = props
                        # This generates the unique list based on the drug's LogP
                        st.session_state.recs = get_unique_recommendations(props)
                else:
                    st.error("Please enter a drug name.")

    # Results Display Area (Only shows if recs exist in session state)
    if st.session_state.recs:
        st.divider()
        st.subheader(f"Top 5 AI-Matched Components for: {st.session_state.drug.upper()}")
        
        # Displaying the molecular properties used for the search
        p = st.session_state.props
        st.caption(f"Molecular Fingerprint: MW: {p['MW']} | LogP: {p['LogP']}")
        
        r = st.session_state.recs
        c1, c2, c3 = st.columns(3)
        
        with c1: 
            st.info("### 💧 Oils")
            for item in r['Oils']: 
                st.markdown(f"- **{item}**")
                
        with c2: 
            st.success("### 🧪 Surfactants")
            for item in r['Surfactants']: 
                st.markdown(f"- **{item}**")
                
        with c3: 
            st.warning("### 🧬 Co-Surfactants")
            for item in r['Co-Surfactants']: 
                st.markdown(f"- **{item}**")
        
        st.write("##") # Vertical spacing
        if st.button("Proceed to Selection ➡️", use_container_width=True, type="primary"):
            st.session_state.step = 2
            st.rerun()

# --- 2. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 1, 'drug': None, 'props': None, 'recs': None,
        'sel_o': '', 'sel_s': '', 'sel_cs': ''
    })

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing & Sizing")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        drug_input = st.text_input("Identify Target Drug", placeholder="e.g. Ibuprofen")
        if st.button("Perform AI Simulation", use_container_width=True):
            if drug_input:
                with st.spinner("Processing chemical fingerprint..."):
                    props = fetch_drug_data(drug_input)
                    st.session_state.drug = drug_input
                    st.session_state.props = props
                    st.session_state.recs = get_unique_recommendations(props)
            else:
                st.error("Enter a drug name.")

    if st.session_state.recs:
        with col2:
            st.subheader(f"Top 5 Recommendations for {st.session_state.drug}")
            r = st.session_state.recs
            c1, c2, c3 = st.columns(3)
            with c1: 
                st.info("**Oils**")
                for item in r['Oils']: st.write(f"• {item}")
            with c2: 
                st.success("**Surfactants**")
                for item in r['Surfactants']: st.write(f"• {item}")
            with c3: 
                st.warning("**Co-Surfactants**")
                for item in r['Co-Surfactants']: st.write(f"• {item}")
        
        st.divider()
        if st.button("Proceed to Selection ➡️", use_container_width=True):
            st.session_state.step = 2; st.rerun()

# --- STEP 2: RADIO SELECTION ---
elif st.session_state.step == 2:
    st.header(f"Step 2: Component Finalization")
    r = st.session_state.recs
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: st.session_state.sel_o = st.radio("Primary Oil Phase", r['Oils'])
    with col_b: st.session_state.sel_s = st.radio("Primary Surfactant", r['Surfactants'])
    with col_c: st.session_state.sel_cs = st.radio("Primary Co-Surfactant", r['Co-Surfactants'])
    
    st.divider()
    b1, b2 = st.columns(2)
    if b1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if b2.button("Generate Final Analysis ➡️", use_container_width=True):
        st.session_state.step = 3; st.rerun()

# --- STEP 3: ANALYTICS & PDF ---
elif st.session_state.step == 3:
    st.header("Step 3: Solubility Analysis & Optimization Report")
    p = st.session_state.props
    
    # Solubility Equations
    logs = 0.16 - (0.63 * p['LogP']) - (0.0062 * p['MW'])
    ee_pred = min(99.8, 70.0 + (p['LogP'] * 4.5))
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted LogS", f"{logs:.3f}")
    m2.metric("Predicted %EE", f"{ee_pred:.1f}%")
    m3.metric("System Stability", "High" if p['LogP'] > 2.5 else "Moderate")

    # Feature Visualization (SHAP-style)
    fig, ax = plt.subplots(figsize=(8, 3))
    features = ["LogP Impact", "MW Steric", "Lipid Affinity", "Solvent Synergy"]
    impacts = [-0.63, -0.12, 0.45, 0.38]
    ax.barh(features, impacts, color=['#e74c3c', '#e67e22', '#2ecc71', '#3498db'])
    ax.set_title("Solubility Driver Analysis")
    st.pyplot(fig); plt.savefig("plot.png")

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "NanoPredict Pro Technical Report", 0, 1, 'C'); pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Drug: {st.session_state.drug}", 0, 1)
        pdf.cell(0, 10, f"Formulation: {st.session_state.sel_o} / {st.session_state.sel_s} / {st.session_state.sel_cs}", 0, 1)
        pdf.ln(5); pdf.image("plot.png", x=10, w=180)
        return pdf.output(dest='S').encode('latin-1')

    st.download_button("Download Technical Report (PDF)", generate_pdf(), f"{st.session_state.drug}_Report.pdf", "application/pdf", use_container_width=True)
    
    if st.button("Start New Analysis 🔄", use_container_width=True):
        st.session_state.update({'step': 1, 'drug': None, 'recs': None})
        st.rerun()
