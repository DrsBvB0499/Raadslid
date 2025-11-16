import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader # Zorg dat je 'PyPDF2' hebt geïnstalleerd (pip install PyPDF2)
import os

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Analyse Agent",
    page_icon="🤖",
    layout="wide"
)

# --- KERN FUNCTIES ---

def get_pdf_text_with_citations(uploaded_files):
    """
    Leest alle geüploade PDF-bestanden en extraheert de tekst.
    Voegt een duidelijke bronvermelding (bestandsnaam + paginanummer) 
    toe vóór de tekst van elke pagina.
    """
    full_text = ""
    if not uploaded_files:
        return ""
        
    for uploaded_file in uploaded_files:
        try:
            # Sla het geüploade bestand tijdelijk op om een bestandsnaam te hebben
            # (Streamlit's in-memory object heeft een .name)
            filename = uploaded_file.name
            st.write(f"Verwerken van: {filename}...") # Feedback voor de gebruiker

            reader = PdfReader(uploaded_file)
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Dit is de cruciale toevoeging:
                    full_text += f"\n\n--- START BRON: {filename} (Pagina {page_num + 1}) ---\n"
                    full_text += page_text
                    full_text += f"\n--- EINDE BRON: {filename} (Pagina {page_num + 1}) ---\n"
                    
        except Exception as e:
            st.error(f"Fout bij het lezen van {filename}: {e}")
            
    st.write("Alle documenten zijn verwerkt.")
    return full_text

def get_gemini_analysis(api_key, system_prompt, documents_text, user_prompt):
    """
    Configureert de Gemini AI en vraagt om de analyse.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        # Combineer de instructies en documenten voor de AI
        prompt_content = [
            system_prompt,
            f"\n--- SPECIFIEKE OPDRACHT VAN DE GEBRUIKER ---\n{user_prompt}",
            "\n--- START VOLLEDIGE TEKST DOCUMENTEN ---\n" + documents_text
        ]
        
        response = model.generate_content(prompt_content)
        return response.text
    except Exception as e:
        st.error(f"AI-analyse mislukt: {e}")
        return None

# --- DE "SYSTEM PROMPT" (DE HERSENEN VAN DE AI) ---
# Deze prompt definieert de output-kwaliteit, taal, en citatie-eisen.
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


# --- APPLICATIE STRUCTUUR (WIZARD-STIJL) ---

# Initialiseer de 'page' state als deze nog niet bestaat
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'final_analysis' not in st.session_state:
    st.session_state.final_analysis = ""

# Functies om van pagina te wisselen
def set_page(page_num):
    st.session_state.page = page_num

# --- PAGINA 0: "LOGIN" (API KEY) ---
if st.session_state.page == 0:
    st.image("https://g.co/gemini/share/fac302bc8f46", width=150) # Vervang dit met je eigen logo indien gewenst
    st.title("Welkom bij de Analyse Agent")
    st.write("Voer je Google AI (Gemini) API-sleutel in om te beginnen.")

    api_key_input = st.text_input("Gemini API Sleutel", type="password", value=st.session_state.api_key)

    if st.button("Inloggen"):
        if api_key_input:
            st.session_state.api_key = api_key_input
            set_page(1)
        else:
            st.error("Voer alsjeblieft een API-sleutel in.")

# --- PAGINA 1: DOCUMENTEN UPLOADEN ---
elif st.session_state.page == 1:
    st.title("Stap 1: Documenten Uploaden")
    st.write("Upload een of meerdere PDF-bestanden die je wilt analyseren.")
    
    uploaded_files = st.file_uploader(
        "Kies je PDF-bestanden",
        type="pdf",
        accept_multiple_files=True,
        key="uploaded_files"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Terug naar Inloggen"):
            set_page(0)
    with col2:
        if st.button("Volgende Stap: Instructie"):
            if 'uploaded_files' in st.session
