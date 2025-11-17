# core/analysis.py
import streamlit as st
import google.generativeai as genai
from datetime import datetime # --- FIX: Import datetime ---

# --- TECHNICAL SYSTEM PROMPT (HIDDEN FROM USER) ---
# --- FIX: Added "Metagegevens" as the first required step ---
TECHNICAL_PROMPT_RULES = """
**ZEER BELANGRIJKE REGELS VOOR OUTPUT:**

* Je EINDPRODUCT moet een scherp, pragmatisch analyserapport zijn om een raadslid voor te bereiden.
* Je spreekt en schrijft uitsluitend Nederlands.
* Het rapport MOET de volgende *minimale* structuur hebben:

    1.  **Metagegevens:** Start met deze sectie. Maak een lijst (geen tabel) met de volgende 3 punten:
        * **Datum Analyse:** [Gebruik de 'HUIDIGE DATUM' die in de prompt is opgegeven]
        * **Datum Bespreking:** [Schrijf "Niet gespecificeerd in documenten" (tenzij je het echt vindt)]
        * **Geanalyseerde Documenten:** [Lijst de bestandsnamen op die je in de 'START BRON' tags hebt gezien]
    
    2.  **Korte Samenvatting:** Een makkelijk leesbare samenvatting van de belangrijkste punten, in één alinea. (Voor dit onderdeel is *geen* citatie nodig).

    3.  **Risico's en Kansen:** Een lijst van de belangrijkste risico's (financieel, juridisch, maatschappelijk) en kansen die je in de documenten ziet.
    
    4.  **Kritische Vragen:** Een lijst van specifieke, scherpe vragen die het raadslid kan stellen aan de indiener van de stukken.

* **BELANGRIJK: Ruimte voor Eigen Inzicht**
    * Nadat je de bovenstaande 4 verplichte punten hebt voltooid, **moedig ik je aan** om een extra, optionele sectie toe te voegen genaamd `### Overige Observaties en Aanbevelingen`.

* **VERPLICHTE CITATIE REGELS:**
    * De documenten zijn gemarkeerd met '--- START BRON: [bestandsnaam] (Pagina [nummer]) ---'.
    * VOOR ELK punt in 'Risico's en Kansen' en 'Kritische Vragen' (en 'Overige Observaties'), MOET je directe bewijsvoering leveren.
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
        
        model = genai.GenerativeModel('gemini-2.5-pro') 
        
        final_system_prompt = f"""
{persona_prompt}

{TECHNICAL_PROMPT_RULES}
"""
        # --- FIX: Get current date and add it to the prompt ---
        now_str = datetime.now().strftime("%d-%m-%Y")
        
        prompt_content = [
            final_system_prompt,
            f"\n--- HUIDIGE DATUM (voor 'Datum Analyse') ---\n{now_str}",
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
