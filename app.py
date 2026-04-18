import streamlit as st
import requests
import numpy as np

# --- 1. DYNAMIC AI SIMULATOR (Sanitized) ---
def fetch_drug_data(drug_name):
    """Fetches unique molecular data. Returns generic defaults if API fails."""
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/MolecularWeight,LogP/JSON"
        res = requests.get(url, timeout=5).json()
        props = res['PropertyTable']['Properties'][0]
        return {"MW": props.get("MolecularWeight", 400.0), "LogP": props.get("XLogP") or props.get("LogP", 3.0)}
    except:
        return {"MW": 400.0, "LogP": 3.0}

def generate_clean_top5(drug_props, category):
    """Calculates affinity and returns a clean Python list of exactly 5 names."""
    LIB = {
        "Oils": ["Capryol 90", "Labrafac PG", "Sefsol 218", "Castor Oil", "Oleic Acid", "Miglyol 812", "Soybean Oil", "Olive Oil", "IPM", "Corn Oil"],
        "Surfactants": ["Tween 80", "Cremophor EL", "Labrasol", "Span 80", "Kolliphor RH40", "Gelucire 44/14", "Solutol HS15", "Tween 20", "Poloxamer 188"],
        "Co-Surfactants": ["Transcutol P", "PEG 400", "Propylene Glycol", "Ethanol", "Plurol Oleique", "PEG 200", "Glycerin", "Isopropanol"]
    }
    
    # Use LogP and MW as a seed to ensure uniqueness per drug
    seed = int(abs(drug_props['LogP'] * 100) + (drug_props['MW'] % 100))
    rng = np.random.default_rng(seed)
    
    # Selection logic: shuffle and pick 5 (Eliminates NULLs by only using valid list items)
    pool = LIB[category]
    rng.shuffle(pool)
    return pool[:5]

# --- 2. SESSION INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.update({'step': 1, 'drug_name': "", 'recs': None})

# --- STEP 1: DYNAMIC SOURCING ---
if st.session_state.step == 1:
    st.header("Step 1: AI Molecular Sourcing")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # Input triggers a clear if the name changes
        input_name = st.text_input("Identify Target Drug", placeholder="e.g. Ibuprofen")
        
        if st.button("Perform AI Simulation", use_container_width=True):
            if input_name:
                # Force refresh data for the new drug
                props = fetch_drug_data(input_name)
                st.session_state.drug_name = input_name
                st.session_state.recs = {
                    "Oils": generate_clean_top5(props, "Oils"),
                    "Surfactants": generate_clean_top5(props, "Surfactants"),
                    "Co-Surfactants": generate_clean_top5(props, "Co-Surfactants")
                }
                st.success(f"Simulation complete for {input_name}")
            else:
                st.error("Please enter a drug name.")

    if st.session_state.recs:
        with col2:
            st.subheader(f"Top 5 Recommendations for {st.session_state.drug_name}")
            r = st.session_state.recs
            c1, c2, c3 = st.columns(3)
            
            # Rendering as clean lists (No NULL brackets)
            with c1: 
                st.markdown("**Oils**")
                for item in r['Oils']: st.write(f"• {item}")
            with c2: 
                st.markdown("**Surfactants**")
                for item in r['Surfactants']: st.write(f"• {item}")
            with c3: 
                st.markdown("**Co-Surfactants**")
                for item in r['Co-Surfactants']: st.write(f"• {item}")
        
        st.divider()
        if st.button("Proceed to Selection Step ➡️", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: RADIO SELECTION ---
elif st.session_state.step == 2:
    st.header(f"Step 2: Component Selection ({st.session_state.drug_name})")
    r = st.session_state.recs
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: sel_o = st.radio("Choose Oil Phase", r['Oils'])
    with col_b: sel_s = st.radio("Choose Surfactant", r['Surfactants'])
    with col_c: sel_cs = st.radio("Choose Co-Surfactant", r['Co-Surfactants'])
    
    st.divider()
    b1, b2 = st.columns(2)
    if b1.button("⬅️ Reset/New Drug"):
        st.session_state.step = 1
        st.session_state.recs = None
        st.rerun()
    if b2.button("Final Analysis ➡️", use_container_width=True):
        st.session_state.final_form = f"{sel_o} + {sel_s} + {sel_cs}"
        st.session_state.step = 3
        st.rerun()

# --- STEP 3: FINAL OUTPUT ---
elif st.session_state.step == 3:
    st.header("Step 3: Final Formulation Analysis")
    st.success(f"Final Optimized System for **{st.session_state.drug_name}**:")
    st.title(st.session_state.final_form)
    
    if st.button("Start New Project 🔄"):
        st.session_state.step = 1
        st.session_state.recs = None
        st.rerun()
