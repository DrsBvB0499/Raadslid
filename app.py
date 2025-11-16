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
            if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
                set_page(2)
            else:
                st.warning("Upload alsjeblieft eerst een of meerdere PDF-bestanden.")

# --- PAGINA 2: ANALYSE INSTRUCTIE ---
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
    with col2:
        if st.button("Start Analyse (dit kan even duren)"):
            if 'analysis_prompt' in st.session_state and st.session_state.analysis_prompt:
                set_page(3) # Ga naar de resultatenpagina
            else:
                st.warning("Geef alsjeblieft een instructie op.")

# --- PAGINA 3: RESULTATEN ---
elif st.session_state.page == 3:
    st.title("Stap 3: Analyse Resultaten")
    
    # Voer de analyse EENMAAL uit en sla het resultaat op
    if not st.session_state.final_analysis:
        # 1. Controleer of alle benodigde data aanwezig is
        if not st.session_state.api_key:
            st.error("API-sleutel niet gevonden. Ga terug naar de inlogpagina.")
            set_page(0)
        elif 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
            st.error("Geen bestanden gevonden. Ga terug naar de uploadpagina.")
            set_page(1)
        elif 'analysis_prompt' not in st.session_state or not st.session_state.analysis_prompt:
            st.error("Geen analyse-instructie gevonden. Ga terug naar de instructiepagina.")
            set_page(2)
        else:
            # 2. Start de analyse (met spinner)
            with st.spinner("Analyse wordt uitgevoerd... Dit kan enkele minuten duren, afhankelijk van de grootte van de documenten."):
                try:
                    # Stap A: Lees PDF's met citaties
                    st.write("Documenten lezen en voorbereiden...")
                    documents_text = get_pdf_text_with_citations(st.session_state.uploaded_files)
                    
                    if documents_text:
                        # Stap B: Roep de AI aan
                        st.write("AI-analyse gestart...")
                        analysis_result = get_gemini_analysis(
                            st.session_state.api_key,
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
                        st.error("Kon geen tekst uit de documenten lezen.")
                        st.session_state.final_analysis = "Analyse mislukt: geen tekst gevonden."
                
                except Exception as e:
                    st.exception(f"Er is een onverwachte fout opgetreden: {e}")
                    st.session_state.final_analysis = f"Analyse mislukt: {e}"

    # 3. Toon het eindresultaat
    st.markdown("---")
    st.subheader("Uw Volledige Analyse")
    st.markdown(st.session_state.final_analysis)
    
    # Knop om opnieuw te beginnen
    if st.button("Nieuwe Analyse Starten"):
        # Reset alle states behalve de API sleutel
        st.session_state.page = 1
        st.session_state.uploaded_files = []
        st.session_state.analysis_prompt = ""
        st.session_state.final_analysis = ""
        st.rerun() # Forceer een herlading van de pagina
