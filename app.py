import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import zipfile
import io

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Analyse Agent",
    page_icon="🤖",
    layout="wide"
)

# --- CORE FUNCTIONS ---
# (process_uploaded_files and get_gemini_analysis are UNCHANGED from V.06)

def process_uploaded_files(uploaded_files):
    """
    Reads all uploaded files (PDFs and ZIPs) and extracts text.
    For ZIPs, it finds and processes PDFs inside them.
    Adds clear source citations (filename + page number) for all text.
    """
    full_text = ""
    if not uploaded_files:
        return ""
        
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        st.write(f"Verwerken van: {filename}...") 
        
        try:
            if uploaded_file.type == "application/pdf":
                reader = PdfReader(uploaded_file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n\n--- START BRON: {filename} (Pagina {page_num + 1}) ---\n"
                        full_text += page_text
                        full_text += f"\n--- EINDE BRON: {filename} (Pagina {page_num + 1}) ---\n"

            elif uploaded_file.type == "application/zip":
                # Reset buffer position just in case
                uploaded_file.seek(0)
                with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zf:
                    for internal_file_info in zf.infolist():
                        if internal_file_info.is_dir() or not internal_file_info.filename.lower().endswith('.pdf'):
                            continue
                        
                        internal_filename = internal_file_info.filename
                        st.write(f"  ... Verwerken (in ZIP): {internal_filename}") 
                        
                        with zf.open(internal_file_info) as pdf_file_in_zip:
                            pdf_stream = io.BytesIO(pdf_file_in_zip.read())
                            try:
                                reader = PdfReader(pdf_stream)
                                for page_num, page in enumerate(reader.pages):
                                    page_text = page.extract_text()
                                    if page_text:
                                        citation_name = f"{filename} -> {internal_filename}"
                                        full_text += f"\n\n--- START BRON: {citation_name} (Pagina {page_num + 1}) ---\n"
                                        full_text += page_text
                                        full_text += f"\n--- EINDE BRON: {citation_name} (Pagina {page_num + 1}) ---\n"
                            except Exception as e_pdf:
                                st.warning(f"Kon {internal_filename} in de ZIP niet lezen: {e_pdf}") 
                                
        except Exception as e_file:
            st.error(f"Fout bij het lezen van {filename}: {e_file}") 
            
    st.write("Alle documenten zijn verwerkt.") 
    return full_text

def get_gemini_analysis(system_prompt, documents_text, user_prompt):
    """
    Configures the Gemini AI and requests the analysis.
    Securely fetches the API key from Streamlit Secrets.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        prompt_content = [
            system_prompt,
            f"\n--- SPECIFIEKE OPDRACHT VAN DE GEBRUIKER ---\n{user_prompt}", 
            "\n--- START VOLLEDIGE TEKST DOCUMENTEN ---\n" + documents_text
        ]
        
        response = model.generate_content(prompt_content)
        return response.text
    except KeyError:
        st.error("Fout: 'GEMINI_API_KEY' niet gevonden in Streamlit Secrets. Zorg dat deze correct is ingesteld.")
        return None
    except Exception as e:
        st.error(f"AI-analyse mislukt: {e}") 
        return None

# --- SYSTEM PROMPT (BRAINS OF THE AI) ---
# (UNCHANGED)
SYSTEM_PROMPT_NL = """
Jij bent een deskundige, professionele analist. Je spreekt en schrijft uitsluitend Nederlands.
Je taak is om de verstrekte documenten diepgaand te analyseren. Deze documenten zijn gemarkeerd met '--- START BRON: [bestandsnaam] (Pagina [nummer]) ---'.
Je EINDPRODUCT moet een formeel analyserapport zijn. Beperk jezelf niet; de analyse moet volledig en uitgebreid zijn en alle verstrekte tekst dekken.

Het rapport MOET de volgende structuur hebben:
1.  **Management Samenvatting:** Een korte, krachtige samenvatting (maximaal één alinea) van de belangrijkste bevindingen en conclusies.
2.  **Diepgaande Analyse:** Een gedetailleerde bespreking van alle belangrijke punten, risico's, kansen, tegenstrijdigheden en opmerkelijke feiten die je in de documenten hebt gevonden.
3.  **Aanbevelingen:** Een lijst van concrete, bruikbare aanbevelingen op basis van je analyse.

**ZEER BELANGRIJKE REGELS VOOR CITATIE (VERPLICHT):**
* VOOR ELK PUNT, BEVINDING OF CONCLUSIE die je maakt in de 'Diepgaande Analyse', MOET je directe bewijsvoering leveren.
* Deze bewijsvoering moet de volgende exacte structuur hebben:
    * Je stelling (bijv. "Er is een potentieel budgetrisico geïdentificeerd.")
    * De bronvermelding, direct erna: `(Bron: [bestandsnaam], Pagina [nummer])`
    * Het exacte citaat, op een nieuwe regel:
        > **Citaat:** "...[de letterlijke tekst uit het document die je stelling bewijst]..."
* Baseer je analyse *uitsluitend* op de verstrekte tekst. Maak geen aannames buiten de documenten.
* Zorg dat je antwoord volledig in het Nederlands is.
"""

# --- APPLICATION STRUCTURE (WIZARD-STYLE) ---

# Initialize states
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'final_analysis' not in st.session_state:
    st.session_state.final_analysis = ""
# --- FIX: New state variable for our files ---
if 'file_cache' not in st.session_state:
    st.session_state.file_cache = []

# Helper functions
def set_page(page_num):
    st.session_state.page = page_num

def logout():
    st.session_state.logged_in = False
    st.session_state.page = 0
    st.session_state.final_analysis = ""
    # --- FIX: Clear our new file_cache ---
    st.session_state.file_cache = []
    if 'analysis_prompt' in st.session_state:
        st.session_state.analysis_prompt = ""

# --- PAGE 0: "LOGIN" (APP PASSWORD) ---
# (UNCHANGED)
if not st.session_state.logged_in:
    st.image("https://g.co/gemini/share/fac302bc8f46", width=150) 
    st.title("Welkom bij de Analyse Agent")
    st.write("Voer het wachtwoord in om de applicatie te gebruiken.")
    password_input = st.text_input("Wachtwoord", type="password", key="login_password") 

    if st.button("Inloggen"): 
        try:
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                set_page(1)
                st.rerun()
            else:
                st.error("Wachtwoord onjuist.") 
        except KeyError:
            st.error("Fout: 'APP_PASSWORD' niet gevonden in Streamlit Secrets. De applicatie is niet correct geconfigureerd.")
        except Exception as e:
            st.error(f"Er is een fout opgetreden: {e}") 

# --- MAIN APPLICATION (POST-LOGIN) ---
else:
    # --- PAGE 1: DOCUMENT UPLOAD ---
    if st.session_state.page == 1:
        st.title("Stap 1: Documenten Uploaden")
        st.write("Upload een of meerdere PDF-bestanden die je wilt analyseren. Je kunt ook een ZIP-bestand uploaden dat PDF's bevat.")
        
        # --- FIX: Remove key= and just use the widget's return value ---
        uploaded_files_widget = st.file_uploader(
            "Kies je PDF- of ZIP-bestanden",
            type=["pdf", "zip"],
            accept_multiple_files=True,
            # We use our own cache, so we can set the default to that
            value=st.session_state.file_cache  
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Uitloggen"): 
                logout()
                st.rerun()
        with col2:
            # --- FIX: Logic changed to use the widget variable ---
            if st.button("Volgende Stap: Instructie"): 
                if uploaded_files_widget:
                    # Manually save the files to our cache
                    st.session_state.file_cache = uploaded_files_widget
                    set_page(2)
                    st.rerun()
                else:
                    # Clear the cache if the user removed all files
                    st.session_state.file_cache = [] 
                    st.warning("Upload alsjeblieft eerst een of meerdere bestanden.") 

    # --- PAGE 2: ANALYSIS PROMPT ---
    # (UNCHANGED)
    elif st.session_state.page == 2:
        st.title("Stap 2: Analyse Instructie")
        st.write("De AI zal de documenten analyseren en zoeken naar de punten die jij opgeeft. De AI zal *altijd* een samenvatting, analyse en aanbevelingen geven.")
        default_prompt = "Analyseer de documenten. Focus op de belangrijkste risico's, financiële verplichtingen en eventuele tegenstrijdigheden tussen de documenten."
        user_prompt = st.text_area(
            "Geef hier je specifieke analyse-opdracht:", 
            value=default_prompt,
            height=150,
            key="analysis_prompt"
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

    # --- PAGE 3: RESULTS ---
    elif st.session_state.page == 3:
        st.title("Stap 3: Analyse Resultaten")
        
        if not st.session_state.final_analysis:
            # --- FIX: Check our 'file_cache' instead of 'uploaded_files' ---
            if 'file_cache' not in st.session_state or not st.session_state.file_cache:
                st.error("Geen bestanden gevonden. Ga terug naar de uploadpagina.") 
                set_page(1)
            # (End fix)
            
            elif 'analysis_prompt' not in st.session_state or not st.session_state.analysis_prompt:
                st.error("Geen analyse-instructie gevonden. Ga terug naar de instructiepagina.") 
                set_page(2)
            else:
                with st.spinner("Analyse wordt uitgevoerd... Dit kan enkele minuten duren, afhankelijk van de grootte van de documenten."): 
                    try:
                        st.write("Documenten lezen en voorbereiden...") 
                        
                        # --- FIX: Process files from our 'file_cache' ---
                        documents_text = process_uploaded_files(st.session_state.file_cache)
                        
                        if documents_text:
                            st.write("AI-analyse gestart...") 
                            analysis_result = get_gemini_analysis(
                                SYSTEM_PROMPT_NL,
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

        # 3. Display the final result
        st.markdown("---")
        st.subheader("Uw Volledige Analyse") 
        st.markdown(st.session_state.final_analysis)
        
        if st.button("Nieuwe Analyse Starten"): 
            st.session_state.page = 1
            # --- FIX: Clear our 'file_cache' ---
            st.session_state.file_cache = []
            st.session_state.analysis_prompt = ""
            st.session_state.final_analysis = ""
            st.rerun() 
        
        if st.button("Uitloggen"): 
            logout()
            st.rerun()
