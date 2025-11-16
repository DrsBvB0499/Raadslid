# app.py
import streamlit as st
import os
from core.auth import check_password, logout
from core.file_processing import process_uploaded_files
from core.analysis import get_gemini_analysis
# --- FIX: Import our new HTML function ---
from core.output import create_html_download 

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Analyse Agent",
    page_icon="🤖",
    layout="wide"
)

# --- STATE INITIALISATIE ---
# (Dit hele blok is ongewijzigd)
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'final_analysis' not in st.session_state:
    st.session_state.final_analysis = ""
if 'file_cache' not in st.session_state:
    st.session_state.file_cache = []
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = None

default_persona = ("Jij bent een ervaren lokaal politicus en senior gemeenteraadslid "
                   "voor een lokale politieke partij. Jouw partij richt zich op 'de "
                   "goede dingen doen en de dingen goed doen' voor de gemeenschap. Je bent "
                   "pragmatisch, financieel verantwoordelijk en gemeenschapsgericht.")
default_instructions = ("Analyseer de volgende documenten voor een gemeenteraadsvergadering.")

if 'persona_prompt' not in st.session_state:
    st.session_state.persona_prompt = default_persona
if 'instructions_prompt' not in st.session_state:
    st.session_state.instructions_prompt = default_instructions


# --- HELPER FUNCTIES ---
# (Dit blok is ongewijzigd)
def set_page(page_num):
    st.session_state.page = page_num

def save_files_to_cache():
    """Callback: Syncs the file uploader widget to our file_cache state."""
    st.session_state.file_cache = st.session_state.file_uploader_key


# --- PAGINA 0: "LOGIN" ---
# (Deze pagina is ongewijzigd)
if not st.session_state.logged_in:
    st.image("https://g.co/gemini/share/fac302bc8f46", width=150) 
    st.title("Welkom bij de Analyse Agent")
    st.write("Voer het wachtwoord in om de applicatie te gebruiken.")
    check_password()

# --- HOOFD APPLICATIE (NA INLOGGEN) ---
else:
    # --- PAGINA 1: DOCUMENTEN UPLOADEN ---
    # (Deze pagina is ongewijzigd)
    if st.session_state.page == 1:
        st.title("Stap 1: Documenten Uploaden")
        st.write("Upload een of meerdere PDF-bestanden die je wilt analyseren. Je kunt ook een ZIP-bestand uploaden dat PDF's bevat.")
        
        st.file_uploader(
            "Kies je PDF- of ZIP-bestanden",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            key="file_uploader_key",
            on_change=save_files_to_cache
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Uitloggen"): 
                logout()
                st.rerun()
        with col2:
            if st.button("Volgende Stap: Instructie"): 
                if st.session_state.file_cache:
                    set_page(2)
                    st.rerun()
                else:
                    st.warning("Upload alsjeblieft eerst een of meerdere bestanden.") 

    # --- PAGINA 2: ANALYSE INSTRUCTIE ---
    # (Deze pagina is ongewijzigd)
    elif st.session_state.page == 2:
        st.title("Stap 2: Analyse Instructie")
        st.write("Pas hier de persona van de AI en je specifieke opdracht aan.")
        
        persona_value = st.text_area(
            "Generieke Persona:", 
            value=st.session_state.persona_prompt,
            height=150
        )
        st.session_state.persona_prompt = persona_value

        instructions_value = st.text_area(
            "Specifieke Instructies voor deze Analyse:", 
            value=st.session_state.instructions_prompt,
            height=150
        )
        st.session_state.instructions_prompt = instructions_value

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Terug naar Upload"): 
                set_page(1)
                st.rerun()
        with col2:
            if st.button("Start Analyse (dit kan even duren)"): 
                if st.session_state.persona_prompt and st.session_state.instructions_prompt:
                    set_page(3) 
                    st.rerun()
                else:
                    st.warning("Zorg dat beide instructievelden zijn ingevuld.") 

    # --- PAGINA 3: RESULTATEN ---
    elif st.session_state.page == 3:
        st.title("Stap 3: Analyse Resultaten")
        
        # (Dit analyse-blok is ongewijzigd)
        if not st.session_state.final_analysis:
            if not st.session_state.file_cache:
                st.error("Geen bestanden gevonden. Ga terug naar de uploadpagina.") 
                set_page(1)
            elif not st.session_state.persona_prompt or not st.session_state.instructions_prompt:
                st.error("Geen analyse-instructies gevonden. Ga terug naar de instructiepagina.") 
                set_page(2)
            else:
                with st.spinner("Analyse wordt uitgevoerd... Dit kan enkele minuten duren."): 
                    try:
                        st.write("Documenten lezen en voorbereiden...") 
                        documents_text = process_uploaded_files(st.session_state.file_cache)
                        
                        if documents_text:
                            st.write("AI-analyse gestart...") 
                            
                            analysis_result = get_gemini_analysis(
                                st.session_state.persona_prompt,
                                st.session_state.instructions_prompt,
                                documents_text
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
        
        # --- FIX: Vervang de .txt knop door de .html knop ---
        if st.session_state.final_analysis:
            # Creëer de HTML-inhoud
            html_content = create_html_download(
                st.session_state.final_analysis,
                title="Analyse Raadsstukken"
            )
            st.download_button(
                label="Download Analyse (.html)",
                data=html_content,           # De HTML-string
                file_name="analyse.html",    # De bestandsnaam
                mime="text/html"             # Het bestandstype
            )
        
        if st.button("Nieuwe Analyse Starten"): 
            st.session_state.page = 1
            st.session_state.file_cache = []
            st.session_state.file_uploader_key = None
            st.session_state.final_analysis = ""
            st.rerun() 
        
        if st.button("Uitloggen"): 
            logout()
            st.rerun()
