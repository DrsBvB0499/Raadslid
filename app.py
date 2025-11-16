# app.py
import streamlit as st
import os
from core.auth import check_password, logout
from core.file_processing import process_uploaded_files
from core.analysis import get_gemini_analysis

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Analyse Agent",
    page_icon="🤖",
    layout="wide"
)

# --- STATE INITIALISATIE ---
# Initialiseer de 'page' state als deze nog niet bestaat
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'final_analysis' not in st.session_state:
    st.session_state.final_analysis = ""
# Dit is onze permanente, veilige opslag voor bestanden
if 'file_cache' not in st.session_state:
    st.session_state.file_cache = []
# Dit is de key voor de uploader widget zelf
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = None


# --- HELPER FUNCTIES ---
def set_page(page_num):
    st.session_state.page = page_num

# --- FIX: Dit is de correcte manier om de callback te schrijven ---
def save_files_to_cache():
    """
    Deze callback leest de bestanden uit de widget-state 
    en slaat ze op in onze permanente 'file_cache' state.
    Dit voorkomt de 'StreamlitValueAssignmentNotAllowedError'.
    """
    st.session_state.file_cache = st.session_state.file_uploader_key


# --- PAGINA 0: "LOGIN" ---
if not st.session_state.logged_in:
    st.image("https://g.co/gemini/share/fac302bc8f46", width=150) 
    st.title("Welkom bij de Analyse Agent")
    st.write("Voer het wachtwoord in om de applicatie te gebruiken.")
    # De check_password functie handelt nu de logica af
    check_password()

# --- HOOFD APPLICATIE (NA INLOGGEN) ---
else:
    # --- PAGINA 1: DOCUMENTEN UPLOADEN ---
    if st.session_state.page == 1:
        st.title("Stap 1: Documenten Uploaden")
        st.write("Upload een of meerdere PDF-bestanden die je wilt analyseren. Je kunt ook een ZIP-bestand uploaden dat PDF's bevat.")
        
        # De file uploader gebruikt nu de callback correct
        st.file_uploader(
            "Kies je PDF- of ZIP-bestanden",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="file_uploader_key",       # De key van de widget
            on_change=save_files_to_cache  # De callback-functie
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Uitloggen"): 
                logout()
                st.rerun()
        with col2:
            # We controleren nu onze veilige 'file_cache'
            if st.button("Volgende Stap: Instructie"): 
                if st.session_state.file_cache: # Check onze betrouwbare cache
                    set_page(2)
                    st.rerun()
                else:
                    st.warning("Upload alsjeblieft eerst een of meerdere bestanden.") 

    # --- PAGINA 2: ANALYSE INSTRUCTIE ---
    elif st.session_state.page == 2:
        st.title("Stap 2: Analyse Instructie")
        st.write("De AI zal de documenten analyseren en zoeken naar de punten die jij opgeeft. De AI zal *altijd* een samenvatting, analyse en aanbevelingen geven.")
        
        default_prompt = "Analyseer de documenten. Focus op de belangrijkste risico's, financiële verplichtingen en eventuele tegenstrijdigheden tussen de documenten."
        
        st.text_area(
            "Geef hier je specifieke analyse-opdracht:", 
            value=default_prompt,
            height=150,
            key="analysis_prompt" # Slaat dit automatisch op in session_state
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Terug naar Upload"): 
                set_page(1)
                st.rerun()
        with col2:
            if st.button("Start Analyse (dit kan even duren)"): 
                if 'analysis_prompt' in st.session_state and st.session_state.analysis_prompt:
                    set_page(3) 
                    st.rerun()
                else:
                    st.warning("Geef alsjeblieft een instructie op.") 

    # --- PAGINA 3: RESULTATEN ---
    elif st.session_state.page == 3:
        st.title("Stap 3: Analyse Resultaten")
        
        # Voer de analyse EENMAAL uit
        if not st.session_state.final_analysis:
            # Controleer onze veilige 'file_cache'
            if not st.session_state.file_cache:
                st.error("Geen bestanden gevonden. Ga terug naar de uploadpagina.") 
                set_page(1)
            elif not st.session_state.analysis_prompt:
                st.error("Geen analyse-instructie gevonden. Ga terug naar de instructiepagina.") 
                set_page(2)
            else:
                # Start de analyse
                with st.spinner("Analyse wordt uitgevoerd... Dit kan enkele minuten duren, afhankelijk van de grootte van de documenten."): 
                    try:
                        st.write("Documenten lezen en voorbereiden...") 
                        
                        # 1. Roep de file processing functie aan
                        documents_text = process_uploaded_files(st.session_state.file_cache)
                        
                        if documents_text:
                            st.write("AI-analyse gestart...") 
                            
                            # 2. Roep de analyse functie aan
                            analysis_result = get_gemini_analysis(
                                documents_text,
                                st.session_state.analysis_prompt
                            )
                            if analysis_result:
                                st.session_state.final_analysis = analysis_result
                                st.success("Analyse voltooid!") 
                            else:
                                st.error("De AI kon geen resultaat genereren.") 
                                st.session_state.final_analysis = "Analyse mislukt." 
                        else:
                            st.error("Kon geen tekst uit de documenten lezen. Zorg dat de bestanden (of ZIPs) leesbare PDF's bevatten.") 
                            st.session_state.final_analysis = "Analyse mislukt: geen tekst gevonden." 
                    
                    except Exception as e:
                        st.exception(f"Er is een onverwachte fout opgetreden: {e}")
                        st.session_state.final_analysis = f"Analyse mislukt: {e}" 

        # Toon het eindresultaat
        st.markdown("---")
        st.subheader("Uw Volledige Analyse") 
        st.markdown(st.session_state.final_analysis)
        
        if st.button("Nieuwe Analyse Starten"): 
            st.session_state.page = 1
            st.session_state.file_cache = []
            st.session_state.file_uploader_key = None # or []
            st.session_state.analysis_prompt = ""
            st.session_state.final_analysis = ""
            st.rerun() 
        
        if st.button("Uitloggen"): 
            logout()
            st.rerun()
