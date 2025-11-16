# core/auth.py
import streamlit as st

def check_password():
    """Returns True if user has entered the correct password."""
    
    password_input = st.text_input("Wachtwoord", type="password", key="login_password") 

    if st.button("Inloggen"): 
        try:
            # Check the password against the English-named secret
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
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
    st.session_state.file_uploader_key = None # or []
    if 'analysis_prompt' in st.session_state:
        st.session_state.analysis_prompt = ""
