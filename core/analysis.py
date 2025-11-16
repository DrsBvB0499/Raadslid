# core/analysis.py
import streamlit as st
import google.generativeai as genai

# --- TECHNICAL SYSTEM PROMPT (HIDDEN FROM USER) ---
# --- FIX: Added Summary and Optional "Other Observations" section ---
TECHNICAL_PROMPT_RULES = """
**ZEER BELANGRIJKE REGELS VOOR OUTPUT:**

* Je EINDPRODUCT moet een scherpe, pragmatische analyse zijn om een raadslid voor te bereiden.
* Je spreekt en schrijft uitsluitend Nederlands.
* Het rapport MOET de volgende *minimale* structuur hebben:
    1.  **Korte Samenvatting:** Een makkelijk leesbare samenvatting van de belangrijkste punten, in één alinea. (Voor dit onderdeel is *geen* citatie nodig).
    2.  **Risico's en Kansen:** Een lijst van de belangrijkste risico's (financieel, juridisch, maatschappelijk) en kansen die je in de documenten ziet.
    3.  **Kritische Vragen:** Een lijst van specifieke, scherpe vragen die het raadslid kan stellen aan de indiener van de stukken.

* **BELANGRIJK: Ruimte voor Eigen Inzicht**
    * Nadat je de bovenstaande 3 verplichte punten hebt voltooid, **moedig ik je aan** om een extra, optionele sectie toe te voegen genaamd `### Overige Observaties en Aanbevelingen`.
    * Gebruik deze sectie als je (vanuit jouw rol als raadslid) aanvullende informatie, aanbevelingen of strategische inzichten hebt die niet direct onder 'Risico's' of 'Vragen' vallen, maar wel cruciaal zijn.

* **VERPLICHTE CITATIE REGELS:**
    * De documenten zijn gemarkeerd met '--- START BRON: [bestandsnaam] (Pagina [nummer]) ---'.
    * VOOR ELK punt in 'Risico's en Kansen' en 'Kritische Vragen', MOET je directe bewijsvoering leveren.
    * Deze bewijsvoering moet de volgende exacte structuur hebben:
        * Je stelling (bijv. "De financiële dekking voor fase 3 lijkt onvolledig.")
        * De bronvermelding, direct erna: `(Bron: [bestandsnaam], Pagina [nummer])`
        * Het exacte citaat, op een nieuwe regel:
            > **Citaat:** "...[de letterlijke tekst uit het document die je stelling bewijst]..."
* Baseer je analyse *uitsluitend* op de verstrekte tekst.
"""

def get_gemini_analysis(persona_prompt, instructions_prompt, documents_text):
    """
    Configureert de Gemini AI en vraagt om de analyse.
    Combineert de persona, instructies en technische regels.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Correct model name
        model = genai.GenerativeModel('gemini-2.5-pro') 
        
        # Combine all prompts into the final system instruction
        final_system_prompt = f"""
{persona_prompt}

{TECHNICAL_PROMPT_RULES}
"""
        
        prompt_content = [
            final_system_prompt,
            f"\n--- SPECIFIEKE OPDRACHT VAN DE GEBRUIKER ---\n{instructions_prompt}", 
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
