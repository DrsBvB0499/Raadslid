import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Analyse Agent",
    page_icon="🤖",
    layout="wide"
)

# --- CORE FUNCTIONS ---

def get_pdf_text_with_citations(uploaded_files):
    """
    Reads all uploaded PDF files and extracts text.
    Adds a clear source citation (filename + page number) 
    before the text of each page.
    """
    full_text = ""
    if not uploaded_files:
        return ""
        
    for uploaded_file in uploaded_files:
        try:
            filename = uploaded_file.name
            st.write(f"Verwerken van: {filename}...") # Dutch: User feedback

            reader = PdfReader(uploaded_file)
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # This is the crucial part for citations
                    full_text += f"\n\n--- START BRON: {filename} (Pagina {page_num + 1}) ---\n"
                    full_text += page_text
                    full_text += f"\n--- EINDE BRON: {filename} (Pagina {page_num + 1}) ---\n"
                    
        except Exception as e:
            st.error(f"Fout bij het lezen van {filename}: {e}") # Dutch: User feedback
            
    st.write("Alle documenten zijn verwerkt.") # Dutch: User feedback
    return full_text

def get_gemini_analysis(system_prompt, documents_text, user_prompt):
    """
    Configures the Gemini AI and requests the analysis.
    Securely fetches the API key from Streamlit Secrets.
    """
    try:
        # Securely fetch the API key from secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        prompt_content = [
            system_prompt,
            f"\n--- SPECIFIEKE OPDRACHT VAN DE GEBRUIKER ---\n{user_prompt}", # Dutch: Part of the prompt
            "\n--- START VOLLEDIGE TEKST DOCUMENTEN ---\n" + documents_text  # Dutch: Part of the prompt
        ]
        
        response = model.generate_content(prompt_content)
        return response.text
    except KeyError:
        # User-facing error message in Dutch
        st.error("Fout: 'GEMINI_API_KEY' niet gevonden in Streamlit Secrets. Zorg dat deze correct is ingesteld.")
        return None
    except Exception as e:
        st.error(f"AI-analyse mislukt: {e}") # Dutch: User feedback
        return None

# --- SYSTEM PROMPT (BRAINS OF THE AI) ---
# This prompt remains in Dutch to force the AI's output to be Dutch.
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

# Helper functions for page navigation
def set_page(page_num):
    st.session_state.page = page_num

def logout():
    st.session_state.logged_in = False
    st.session_state.page = 0
    st.session_state.final_analysis = ""
    # Reset other states if they exist
    if 'uploaded_files' in st.session_state:
        st.session_state.uploaded_files = []
    if 'analysis_prompt' in st.session_state:
        st.session_state.analysis_prompt = ""

# --- PAGE 0: "LOGIN" (APP PASSWORD) ---
if not st.session_state.logged_in:
    st.image("https://g.co/gemini/share/fac302bc8f46", width=150) # Replace with your logo if desired
    st.title("Welkom bij de Analyse Agent")
    st.write("Voer het wachtwoord in om de applicatie te gebruiken.")

    password_input = st.text_input("Wachtwoord", type="password", key="login_password") # Dutch label

    if st.button("Inloggen"): # Dutch button
        try:
            # Check the password against the English-named secret
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                set_page(1)
                st.rerun()
            else:
                st.error("Wachtwoord onjuist.") # Dutch error
        except KeyError:
            # Dutch error, but references the correct backend secret name
            st.error("Fout: 'APP_PASSWORD' niet gevonden in Streamlit Secrets. De applicatie is niet correct geconfigureerd.")
        except Exception as e:
            st.error(f"Er is een fout opgetreden: {e}") # Dutch error

# --- MAIN APPLICATION (POST-LOGIN) ---
else:
    # --- PAGE 1: DOCUMENT UPLOAD ---
    if st.session_state.page == 1:
        st.title("Stap 1: Documenten Uploaden")
        st.write("Upload een of meerdere PDF-bestanden die je wilt analyseren.")
        
        uploaded_files = st.file_uploader(
            "Kies je PDF-bestanden", # Dutch label
            type="pdf",
            accept_multiple_files=True,
            key="uploaded_files"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Uitloggen"): # Dutch button
                logout()
                st.rerun()
        with col2:
            if st.button("Volgende Stap: Instructie"): # Dutch button
                if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
