import streamlit as st
import requests
import numpy as np

# --- 1. DYNAMIC AI SIMULATOR ---
def fetch_drug_data(drug_name):
    """Fetches unique molecular data from PubChem."""
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/MolecularWeight,LogP/JSON"
        res = requests.get(url, timeout=5).json()
        props = res['PropertyTable']['Properties'][0]
        return {"MW": props.get("MolecularWeight", 400.0), "LogP": props.get("XLogP") or props.get("LogP", 3.0)}
    except:
        return {"MW": 400.0, "LogP": 3.0}

def generate_clean_top5(drug_props, category):
    """Generates a unique, non-null list of 5 excipients."""
    LIB = {
        "Oils": ["Capryol 90", "Labrafac PG", "Sefsol 218", "Castor Oil", "Oleic Acid", "Miglyol 812", "Soybean Oil", "Olive Oil", "IPM", "Corn Oil"],
        "Surfactants": ["Tween 80", "Cremophor EL", "Labrasol", "Span 80", "Kolliphor RH40", "Gelucire 44/14", "Solutol HS15", "Tween 20", "Poloxamer 188"],
        "Co-Surfactants": ["Transcutol P", "PEG 400", "Propylene Glycol", "Ethanol", "Plurol Oleique", "PEG 200", "Glycerin", "Isopropanol"]
    }
    # Unique seed based on drug properties
    seed = int(abs(drug_props['LogP'] * 100) + (drug_props['MW'] % 100))
    rng = np.random.default_rng(seed)
    pool = list(LIB[category])
    rng.shuffle(pool)
    return pool[:5]

# --- 2. SESSION INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.update({'step': 1, 'drug_name': None, 'recs': None})

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        input_name = st.text_input("Identify Target Drug", placeholder="e.g. Ibuprofen")
        if st.button("Perform AI Simulation", use_container_width=True):
            if input_name:
                with st.spinner("Analyzing..."):
                    props = fetch_drug_data(input_name)
                    st.session_state.drug_name = input_name
                    st.session_state.recs = {
                        "Oils": generate_clean_top5(props, "Oils"),
                        "Surfactants": generate_clean_top5(props, "Surfactants"),
                        "Co-Surfactants": generate_clean_top5(props, "Co-Surfactants")
                    }
            else:
                st.error("Please enter a drug name.")

    # Fix: Only show results if drug_name exists in session_state
    if st.session_state.drug_name and st.session_state.recs:
        with col2:
            st.subheader(f"Top 5 Recommendations for {st.session_state.drug_name}")
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
        if st.button("Proceed to Selection Step ➡️", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: RADIO SELECTION ---
elif st.session_state.step == 2:
    st.header(f"Step 2: Component Selection")
    r = st.session_state.recs
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: sel_o = st.radio("Choose Oil Phase", r['Oils'])
    with col_b: sel_s = st.radio("Choose Surfactant", r['Surfactants'])
    with col_c: sel_cs = st.radio("Choose Co-Surfactant", r['Co-Surfactants'])
    
    st.divider()
    if st.button("Analyze Final Formulation ➡️", use_container_width=True):
        st.session_state.final_choice = f"{sel_o}, {sel_s}, and {sel_cs}"
        st.session_state.step = 3
        st.rerun()

# --- STEP 3: FINAL ANALYSIS ---
elif st.session_state.step == 3:
    st.header("Step 3: Optimization Results")
    st.success(f"Final System for {st.session_state.drug_name}:")
    st.subheader(st.session_state.final_choice)
    if st.button("Start New Analysis 🔄"):
        st.session_state.update({'step': 1, 'drug_name': None, 'recs': None})
        st.rerun()
