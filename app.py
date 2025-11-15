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
                    f"{name}\n{text}" for name, text in document_texts.
