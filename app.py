import streamlit as st
import zipfile
import io
import pdfplumber
import google.generativeai as genai

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Town Hall Assistant",
    layout="centered"
)

# --- 2. AI ANALYSIS FUNCTION ---
def analyze_text(api_key, text_to_analyze, persona_prompt, instructions_prompt):
    """
    Analyzes the text using the Google AI library directly.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        final_prompt = f"""
        {persona_prompt}
        
        {instructions_prompt}
        
        For the provided text, please generate the following:
        
        1.  **Executive Summary:** A very short, high-level summary of the main proposal.
        2.  **Key Issues & Risks:** What are the potential problems, "gotchas", financial risks, or public concerns hidden in this data?
        3.  **Relevant Questions to Ask:** What are 3-5 sharp, insightful questions a politician should ask in the meeting based on these risks?
        
        Here is the text from all the documents:
        ---
        {text_to_analyze} 
        ---
        
        YOUR 1-PAGE BRIEFING:
        """
        
        response = model.generate_content(final_prompt)
        return response.text

    except Exception as e:
        # Return the error message to be displayed on the page
        return f"Error during AI analysis: {e}"

# --- 3. PAGE RENDERING FUNCTIONS ---
# We create a separate function for each "page" to keep the code clean.

def show_login_page():
    """Renders the login page."""
    st.title("Town Hall Assistant")
    st.subheader("Please enter your password to begin.")
    
    password = st.text_input("Password:", type="password")
    
    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            # Correct password. Move to the next page.
            st.session_state.page = "upload"
            st.rerun()
        else:
            st.error("Password incorrect. Please try again.")

def show_upload_page():
    """Renders the file upload page."""
    st.title("Step 1: Upload Documents")
    
    uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")
    
    if uploaded_zip is not None:
        # This is a new file, so clear any old analysis results
        st.session_state.analysis_result = None
        
        with st.spinner("Reading PDF files from ZIP..."):
            document_texts = {} 
            try:
                zip_in_memory = io.BytesIO(uploaded_zip.getvalue())
                with zipfile.ZipFile(zip_in_memory, 'r') as zf:
                    all_files_in_zip = zf.namelist()
                    pdf_files_found = [f for f in all_files_in_zip if f.endswith('.pdf') and not f.startswith('__MACOSX')]
                    
                    for i, file_name in enumerate(pdf_files_found):
                        with zf.open(file_name) as pdf_file_in_zip:
                            with pdfplumber.open(pdf_file_in_zip) as pdf:
                                full_text = ""
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    if text:
                                        full_text += text + "\n\n"
                                document_texts[file_name] = full_text
                
                # Save the combined text to our session state "memory"
                st.session_state.full_document_text = "\n\n--- NEW DOCUMENT: {name} --- \n\n".join(
                    f"{name}\n{text}" for name, text in document_texts.items()
                )
                st.session_state.file_read_success = True
            
            except zipfile.BadZipFile:
                st.error("This does not appear to be a valid file. Please try again.")
                st.session_state.full_document_text = None
                st.session_state.file_read_success = False

        if st.session_state.file_read_success:
            st.success(f"Successfully read and cached {len(document_texts)} PDF document(s).")
            # Move to the next page automatically after reading
            st.session_state.page = "prompting"
            st.rerun()

    if st.button("Logout"):
        st.session_state.page = "login"
        st.rerun()

def show_prompting_page():
    """Renders the prompt customization page."""
    st.title("Step 2: Set Prompts")
    st.info("The text is cached. You can now customize the prompts before analysis.")
    
    default_persona = ("You are a veteran local politician and senior city council member "
                       "for a local political party. Your party focusses on 'doing the "
                       "right things and doing things right' for the community. You are "
                       "pragmatic, financially responsible, and community-focused.")
    st.session_state.persona_prompt = st.text_area(
        "Generic Persona:", 
        value=st.session_state.get("persona_prompt", default_persona), 
        height=150
    )
    
    default_instructions = ("Analyze the following documents for a city council meeting.")
    st.session_state.instructions_prompt = st.text_area(
        "Specific Instructions for this Analysis:", 
        value=st.session_state.get("instructions_prompt", default_instructions), 
        height=150
    )
    
    # --- Action Buttons ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Upload"):
            st.session_state.page = "upload"
            st.rerun()
    with col2:
        if st.button("Start Analysis", type="primary"):
            with st.spinner("🤖 The AI is reading all documents and thinking... This may take a minute..."):
                st.session_state.analysis_result = analyze_text(
                    st.secrets["GOOGLE_API_KEY"], 
                    st.session_state.full_document_text, 
                    st.session_state.persona_prompt, 
                    st.session_state.instructions_prompt
                )
            st.session_state.page = "result"
            st.rerun()

def show_result_page():
    """Renders the final analysis result page."""
    st.title("Step 3: Your Political Briefing")
    
    if st.session_state.analysis_result:
        if st.session_state.analysis_result.startswith("Error during AI analysis:"):
            st.error(st.session_state.analysis_result)
        else:
            st.success("Analysis Complete!")
            st.write(st.session_state.analysis_result)
    else:
        st.warning("No result found. Please go back and try again.")
        
    if st.button("Analyze Another File (Go to Upload)"):
        # Clear the old data and go back to upload
        st.session_state.full_document_text = None
        st.session_state.analysis_result = None
        st.session_state.file_read_success = None
        st.session_state.page = "upload"
        st.rerun()

# --- 4. MAIN APP LOGIC (Page Router) ---
# This is the "bookmark" system that controls which function to run.

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "login"
if "full_document_text" not in st.session_state:
    st.session_state.full_document_text = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "file_read_success" not in st.session_state:
    st.session_state.file_read_success = None

# "Router" - Show the correct page based on the session state
if st.session_state.page == "login":
    show_login_page()
elif st.session_state.page == "upload":
    show_upload_page()
elif st.session_state.page == "prompting":
    show_prompting_page()
elif st.session_state.page == "result":
    show_result_page()
