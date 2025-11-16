# core/analysis.py
import streamlit as st
import google.generativeai as genai

# --- DE "SYSTEM PROMPT" (DE HERSENEN VAN DE AI) ---
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

def get_gemini_analysis(documents_text, user_prompt):
    """
    Configureert de Gemini AI en vraagt om de analyse.
    Haalt de API-sleutel veilig uit Streamlit Secrets.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # --- FIX: Gecorrigeerde modelnaam ---
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt_content = [
            SYSTEM_PROMPT_NL,
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
