import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import hashlib

# --- 1. DYNAMIC AI SIMULATOR ---
def fetch_drug_data(drug_name):
    """Fetches real-time chemical descriptors from PubChem with fallback logic."""
    try:
        clean_name = drug_name.strip().replace(" ", "%20")
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/property/MolecularWeight,XLogP,LogP/JSON"
        res = requests.get(url, timeout=5).json()
        
        if 'PropertyTable' in res:
            props = res['PropertyTable']['Properties'][0]
            mw = props.get("MolecularWeight", 400.0)
            logp = props.get("XLogP") or props.get("LogP", 3.0)
            return {"MW": float(mw), "LogP": float(logp), "found": True}
    except Exception:
        pass
    return {"MW": 400.0, "LogP": 3.0, "found": False}

def calculate_solubility(excipient_name, drug_props):
    """AI heuristic to predict solubility (mg/mL) for a specific drug-excipient pair."""
    # Create a unique offset for each excipient based on its name
    exc_hash = int(hashlib.sha256(excipient_name.encode()).hexdigest(), 16) % 100
    
    # Heuristic: Solubility is higher when drug LogP matches typical lipid ranges
    # We add a bit of 'randomness' (hash) to simulate specific molecular interactions
    base = 15.0 + (drug_props['LogP'] * 2.5) + (exc_hash / 10.0)
    if drug_props['MW'] > 500: base *= 0.7  # Steric hindrance reduces solubility
    
    return round(base, 2)

def get_ranked_recommendations(drug_name, props):
    """Generates unique recommendations ranked by predicted solubility."""
    LIB = {
        "Oils": ["Capryol 90", "Labrafac PG", "Sefsol 218", "Castor Oil", "Oleic Acid", "Miglyol 812", "Soybean Oil", "Olive Oil", "IPM", "Corn Oil", "MCT Oil", "Peanut Oil"],
        "Surfactants": ["Tween 80", "Cremophor EL", "Labrasol", "Span 80", "Kolliphor RH40", "Gelucire 44/14", "Solutol HS15", "Tween 20", "Poloxamer 188", "Pluronic F127"],
        "Co-Surfactants": ["Transcutol P", "PEG 400", "Propylene Glycol", "Ethanol", "Plurol Oleique", "PEG 200", "Glycerin", "Isopropanol", "Butanol", "Menthol"]
    }
    
    name_hash = int(hashlib.sha256(drug_name.lower().encode()).hexdigest(), 16)
    results = {}
    
    for i, (cat, items) in enumerate(LIB.items()):
        seed = (name_hash % 10**8) + i
        rng = np.random.default_rng(seed)
        shuffled = list(items)
        rng.shuffle(shuffled)
        
        # Take 5 and calculate solubility for each
        top_5 = shuffled[:5]
        ranked = []
        for item in top_5:
            sol = calculate_solubility(item, props)
            ranked.append({"name": item, "sol": sol})
        
        # Sort by solubility (mg/mL) Descending
        ranked.sort(key=lambda x: x['sol'], reverse=True)
        results[cat] = ranked
        
    return results

# --- 2. SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 1, 'drug': None, 'props': {}, 'recs': None,
        'sel_o': None, 'sel_s': None, 'sel_cs': None
    })

st.set_page_config(page_title="NanoPredict Pro", layout="wide")
st.title("💊 NanoPredict Pro: AI Formulation Engine")

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing")
    col1, col2 = st.columns([2, 1])
    with col1:
        target_drug = st.text_input("Enter Target Drug Name", placeholder="e.g. Ketoconazole", key="main_input")
    with col2:
        st.write("##") 
        if st.button("Run AI Affinity Simulation", use_container_width=True, type="primary"):
            if target_drug:
                with st.spinner(f"Analyzing {target_drug}..."):
                    props = fetch_drug_data(target_drug)
                    recs = get_ranked_recommendations(target_drug, props)
                    st.session_state.update({'drug': target_drug, 'props': props, 'recs': recs})
            else:
                st.warning("Please enter a drug name.")

    if st.session_state.recs:
        st.divider()
        p = st.session_state.props
        st.subheader(f"Ranked Excipient Compatibility for {st.session_state.drug.upper()}")
        r = st.session_state.recs
        c1, c2, c3 = st.columns(3)
        for i, (cat, col) in enumerate(zip(["Oils", "Surfactants", "Co-Surfactants"], [c1, c2, c3])):
            with col:
                st.markdown(f"### {cat}")
                for item in r[cat]:
                    st.write(f"**{item['name']}**")
                    st.caption(f"Est. Solubility: {item['sol']} mg/mL")

        if st.button("Proceed to Ranked Selection ➡️", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: RANKED SELECTION ---
elif st.session_state.step == 2:
    st.header(f"Step 2: Solubility-Based Selection ({st.session_state.drug})")
    st.info("💡 Components are ranked from Highest to Lowest predicted solubility.")
    r = st.session_state.recs
    
    col_a, col_b, col_c = st.columns(3)
    
    # Format the labels for the radio buttons to show the solubility
    def format_label(opt):
        return f"{opt['name']} ({opt['sol']} mg/mL)"

    with col_a:
        st.session_state.sel_o = st.radio("Primary Oil Phase", r['Oils'], format_func=format_label)
    with col_b:
        st.session_state.sel_s = st.radio("Primary Surfactant", r['Surfactants'], format_func=format_label)
    with col_c:
        st.session_state.sel_cs = st.radio("Primary Co-Surfactant", r['Co-Surfactants'], format_func=format_label)
    
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
    s_o, s_s, s_cs = st.session_state.sel_o, st.session_state.sel_s, st.session_state.sel_cs
    
    # Formula for Total System Solubility
    total_sol = (s_o['sol'] * 0.4) + (s_s['sol'] * 0.4) + (s_cs['sol'] * 0.2)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Selected System Solubility", f"{total_sol:.2f} mg/mL")
    m2.metric("Predicted Encapsulation (%EE)", f"{min(99.8, 70.0 + (p.get('LogP', 3.0) * 4.5)):.1f}%")
    m3.metric("Thermodynamic Stability", "High" if total_sol > 20 else "Moderate")

    # Dynamic Bar Chart
    fig, ax = plt.subplots(figsize=(10, 4))
    labels = [s_o['name'], s_s['name'], s_cs['name']]
    values = [s_o['sol'], s_s['sol'], s_cs['sol']]
    colors = ['#2ecc71', '#3498db', '#f1c40f']
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Solubility (mg/mL)")
    ax.set_title(f"Component Affinity Profile: {st.session_state.drug}")
    st.pyplot(fig)
    
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "NanoPredict Pro Technical Report", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Drug: {st.session_state.drug}", 0, 1)
        pdf.cell(0, 10, f"Selected Oil: {s_o['name']} ({s_o['sol']} mg/mL)", 0, 1)
        pdf.cell(0, 10, f"Selected Surfactant: {s_s['name']} ({s_s['sol']} mg/mL)", 0, 1)
        pdf.cell(0, 10, f"Selected Co-Surfactant: {s_cs['name']} ({s_cs['sol']} mg/mL)", 0, 1)
        pdf.cell(0, 10, f"Total System Sol: {total_sol:.2f} mg/mL", 0, 1)
        
        img_path = "temp_report_plot.png"
        fig.savefig(img_path)
        pdf.image(img_path, x=10, y=80, w=180)
        return pdf.output(dest='S').encode('latin-1')

    st.download_button("Download PDF Report", generate_pdf(), f"{st.session_state.drug}_Report.pdf", "application/pdf", use_container_width=True)
    
    if st.button("Start New Project 🔄", use_container_width=True):
        st.session_state.clear()
        st.rerun()
