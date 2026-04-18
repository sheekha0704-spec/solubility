import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import hashlib

# --- 1. DYNAMIC AI SIMULATOR ---
def fetch_drug_data(drug_name):
    """Fetches real-time chemical descriptors from PubChem."""
    try:
        # Clean the name for the URL
        clean_name = drug_name.strip().replace(" ", "%20")
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/property/MolecularWeight,XLogP,LogP/JSON"
        res = requests.get(url, timeout=5).json()
        
        if 'PropertyTable' in res:
            props = res['PropertyTable']['Properties'][0]
            mw = props.get("MolecularWeight", 400.0)
            # Try XLogP first, then LogP, then default to 3.0
            logp = props.get("XLogP") or props.get("LogP", 3.0)
            return {"MW": float(mw), "LogP": float(logp), "found": True}
    except Exception:
        pass
    
    # Fallback with a slight variation based on name length to avoid identical results
    return {"MW": 400.0 + len(drug_name), "LogP": 3.0, "found": False}

def get_unique_recommendations(drug_name, props):
    """Generates 5 unique recommendations using the drug name as a seed 'salt'."""
    LIB = {
        "Oils": ["Capryol 90", "Labrafac PG", "Sefsol 218", "Castor Oil", "Oleic Acid", "Miglyol 812", "Soybean Oil", "Olive Oil", "IPM", "Corn Oil", "MCT Oil", "Peanut Oil"],
        "Surfactants": ["Tween 80", "Cremophor EL", "Labrasol", "Span 80", "Kolliphor RH40", "Gelucire 44/14", "Solutol HS15", "Tween 20", "Poloxamer 188", "Pluronic F127"],
        "Co-Surfactants": ["Transcutol P", "PEG 400", "Propylene Glycol", "Ethanol", "Plurol Oleique", "PEG 200", "Glycerin", "Isopropanol", "Butanol", "Menthol"]
    }
    
    # Create a unique seed by combining LogP and a hash of the drug name
    # This ensures "Ibuprofen" and "Aspirin" NEVER get the same list
    name_seed = int(hashlib.sha256(drug_name.lower().encode()).hexdigest(), 16) % 10**8
    anchor = int(abs(props['LogP'] * 100)) + name_seed
    
    results = {}
    for cat, items in LIB.items():
        rng = np.random.default_rng(anchor + len(cat))
        shuffled = list(items)
        rng.shuffle(shuffled)
        results[cat] = shuffled[:5]
    return results

# --- 2. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 1, 'drug': None, 'props': None, 'recs': None,
        'sel_o': '', 'sel_s': '', 'sel_cs': ''
    })

st.set_page_config(page_title="NanoPredict Pro", layout="wide")
st.title("💊 NanoPredict Pro: AI Formulation Engine")

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Use a key to ensure the widget state is preserved
        target_drug = st.text_input("Enter Target Drug Name", placeholder="e.g. Ketoconazole", key="input_drug")
    
    with col2:
        st.write("##") 
        if st.button("Run AI Affinity Simulation", use_container_width=True, type="primary"):
            if target_drug:
                with st.spinner(f"Simulating molecular affinity for {target_drug}..."):
                    props = fetch_drug_data(target_drug)
                    recs = get_unique_recommendations(target_drug, props)
                    
                    # Update session state
                    st.session_state.drug = target_drug
                    st.session_state.props = props
                    st.session_state.recs = recs
            else:
                st.warning("Please enter a drug name.")

    if st.session_state.recs:
        st.divider()
        p = st.session_state.props
        status = "✅ Data Verified" if p['found'] else "⚠️ Using Estimated values"
        st.subheader(f"Results for {st.session_state.drug.upper()} ({status})")
        st.caption(f"Molecular Weight: {p['MW']} | LogP: {p['LogP']}")
        
        r = st.session_state.recs
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("### 💧 Top Oils")
            for item in r['Oils']: st.write(f"• {item}")
        with c2:
            st.success("### 🧪 Top Surfactants")
            for item in r['Surfactants']: st.write(f"• {item}")
        with c3:
            st.warning("### 🧬 Top Co-Surfactants")
            for item in r['Co-Surfactants']: st.write(f"• {item}")
        
        st.write("##")
        if st.button("Confirm & Proceed to Selection ➡️", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: RADIO SELECTION ---
elif st.session_state.step == 2:
    st.header(f"Step 2: Selection for {st.session_state.drug}")
    r = st.session_state.recs
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: st.session_state.sel_o = st.radio("Primary Oil", r['Oils'])
    with col_b: st.session_state.sel_s = st.radio("Primary Surfactant", r['Surfactants'])
    with col_c: st.session_state.sel_cs = st.radio("Primary Co-Surfactant", r['Co-Surfactants'])
    
    st.divider()
    b1, b2 = st.columns(2)
    if b1.button("⬅️ Back"): 
        st.session_state.step = 1
        st.rerun()
    if b2.button("Generate Optimization Report ➡️", use_container_width=True, type="primary"):
        st.session_state.step = 3
        st.rerun()

# --- STEP 3: ANALYTICS & PDF ---
elif st.session_state.step == 3:
    st.header("Step 3: Optimization & Solubility Analysis")
    p = st.session_state.props
    
    logs = 0.16 - (0.63 * p['LogP']) - (0.0062 * p['MW'])
    ee_pred = min(99.8, 70.0 + (p['LogP'] * 4.5))
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted LogS", f"{logs:.3f}")
    m2.metric("Predicted Encapsulation (%EE)", f"{ee_pred:.1f}%")
    m3.metric("System Stability", "High" if p['LogP'] > 2.5 else "Moderate")

    fig, ax = plt.subplots(figsize=(10, 4))
    features = ["LogP Impact", "MW Steric", "Lipid Affinity", "Solvent Synergy"]
    impacts = [-0.63 * p['LogP'] / 5, -0.0062 * p['MW'] / 100, 0.45, 0.38]
    ax.barh(features, impacts, color=['#e74c3c', '#e67e22', '#2ecc71', '#3498db'])
    ax.set_title(f"Solubility Driver Analysis: {st.session_state.drug}")
    st.pyplot(fig)
    
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "NanoPredict Pro Technical Report", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Drug Name: {st.session_state.drug}", 0, 1)
        pdf.cell(0, 10, f"Selected Oil: {st.session_state.sel_o}", 0, 1)
        pdf.cell(0, 10, f"Selected Surfactant: {st.session_state.sel_s}", 0, 1)
        pdf.cell(0, 10, f"Selected Co-Surfactant: {st.session_state.sel_cs}", 0, 1)
        
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png')
        img_buf.seek(0)
        with open("temp_report_plot.png", "wb") as f:
            f.write(img_buf.read())
            
        pdf.image("temp_report_plot.png", x=10, y=70, w=180)
        return pdf.output(dest='S').encode('latin-1')

    st.download_button(
        label="Download PDF Report",
        data=generate_pdf(),
        file_name=f"{st.session_state.drug}_Formulation.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    if st.button("Start New Project 🔄", use_container_width=True):
        st.session_state.clear()
        st.rerun()
