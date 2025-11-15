import streamlit as st
import zipfile
import io
import pdfplumber

# --- AI IMPORT ---
import google.generativeai as genai


def analyze_text(api_key, text_to_analyze, persona_prompt, instructions_prompt):
    """
    Analyzes the text using the Google AI library directly,
    with customizable prompts.
    """
    try:
        genai.configure(api_key=api_key)
        
        # --- THE CORRECTED MODEL NAME ---
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # --- DYNAMIC PROMPT ---
        prompt = f"""
        {persona_prompt}
        
        {instructions_prompt}
        
        For the provided text, please generate the following:
        
        1.  **Executive Summary:** A very short, high-level summary of the main proposal.
        2.  **Key Issues & Risks:** What are the potential problems, "gotchas", financial risks, or public concerns hidden in this data?
        3.  **Relevant Questions to Ask:** What are 3-5 sharp, insightful questions a politician should ask in the meeting based on these risks?
        
        Here is the text from all the documents:
        ---
        {text}
        ---
        
        YOUR 1-PAGE BRIEFING:
        """
        
        # Combine the prompt and the text
        final_prompt = prompt.format(text=text_to_analyze)
        
        # Send to the model and get the response
        response = model.generate_content(final_prompt)
        
        return response.text

    except Exception as e:
        st.error(f"Error during AI analysis: {e}")
        return None


# --- Main App Interface ---
st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

# --- Initialize Session State ---
# This creates the "memory" if it doesn't exist
if "full_document_text" not in st.session_state:
    st.session_state.full_document_text = None
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- Password Check ---
password = st.text_input("Enter your app password:", type="password")

if password == st.secrets["APP_PASSWORD"]:
    st.success("Login successful!")
    
    st.subheader("1. Set Prompts (Edit as needed)")
    
    default_persona = ("You are a veteran local politician and senior city council member "
                       "for a local political party. Your party focusses on 'doing the "
                       "right things and doing things right' for the community. You are "
                       "pragmatic, financially responsible, and community-focused.")
    persona_prompt = st.text_area("Generic Persona:", value=default_persona, height=150)
    
    default_instructions = ("Analyze the following documents for a city council meeting. "
                            "This topic has been discussed before, and our party is very "
                            "much opposed to this idea. Analyze the information with "
                            "that stance in mind.")
    instructions_prompt = st.text_area("Specific Instructions for this Analysis:", value=default_instructions, height=150)

    st.subheader("2. Upload and Analyze")
    uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")

    if uploaded_zip is not None:
        
        # --- NEW LOGIC: Only read if it's a NEW file ---
        # We check if the uploaded file is different from the one in memory
        if uploaded_zip.name != st.session_state.last_uploaded_file:
            st.session_state.full_document_text = None # Clear old text
            st.session_state.last_uploaded_file = uploaded_zip.name
            
            document_texts = {} 
            try:
                with st.spinner("Reading PDF files from ZIP..."):
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
                
                # --- NEW: Save the combined text to our "memory" ---
                st.session_state.full_document_text = "\n\n--- NEW DOCUMENT: {name} --- \n\n".join(
                    f"{name}\n{text}" for name, text in document_texts.items()
                )
                st.success(f"Successfully read and cached {len(document_texts)} PDF document(s).")
            
            except zipfile.BadZipFile:
                st.error("This does not appear to be a valid ZIP file. Please try again.")
                st.session_state.full_document_text = None
                st.session_state.last_uploaded_file = None

        # --- Analysis Button ---
        # This part now runs *after* the reading is done (or if text is already cached)
        if st.session_state.full_document_text:
            if st.button("Start Analysis"):
                with st.spinner("🤖 The AI is reading all documents and thinking... This may take a minute..."):
                    
                    # --- NEW: We pull the text from "memory" ---
                    summary_output = analyze_text(
                        st.secrets["GOOGLE_API_KEY"], 
                        st.session_state.full_document_text, # Use the cached text
                        persona_prompt, 
                        instructions_prompt
                    )
                    
                    if summary_output:
                        st.success("Analysis Complete!")
                        st.subheader("Your Political Briefing")
                        st.markdown(summary_output)
                    else:
                        st.error("Analysis failed. Please check the API key in your secrets.")

elif password:
    st.error("Password incorrect. Please try again.")
else:
    st.info("Please enter your password to unlock the assistant.")
