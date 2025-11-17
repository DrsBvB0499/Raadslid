# core/auth.py
import streamlit as st

def check_password():
    """Returns True if user has entered the correct password."""
    
    password_input = st.text_input("Wachtwoord", type="password", key="login_password") 

    if st.button("Inloggen"): 
        try:
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                st.session_state.page = 1
                st.rerun() 
            else:
                st.error("Wachtwoord onjuist.") 
        except KeyError:
            st.error("Fout: 'APP_PASSWORD' niet gevonden in Streamlit Secrets. De applicatie is niet correct geconfigureerd.")
        except Exception as e:
            st.error(f"Er is een fout opgetreden: {e}") 

    return False


def logout():
    """Logs the user out and resets the session."""
    st.session_state.logged_in = False
    st.session_state.page = 0
    st.session_state.final_analysis = ""
    st.session_state.file_cache = []
    st.session_state.file_uploader_key = None
    
    if 'persona_prompt' in st.session_state:
        del st.session_state.persona_prompt
    if 'instructions_prompt' in st.session_state:
        del st.session_state.instructions_prompt
        
    # --- FIX: Add this line to clear the project title ---
    if 'project_title' in st.session_state:
        del st.session_state.project_title
