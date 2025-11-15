import streamlit as st
import zipfile
import io
import pdfplumber

# --- Imports for the AI Brain ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Main App Interface ---
st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

# 1. Ask for the simple app password
password = st.text_input("Enter your app password:", type="password")

# 2. Check if the entered password matches the one in Streamlit Secrets
# We wrap the *entire app* in this check.
if password == st.secrets["APP_PASSWORD"]:
    
    st.success("Login successful!")
    
    # 3. Create the File Uploader (only shows after login)
    uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")

    if uploaded_zip is not None:
        
        # --- Step 1: Read the PDF Text (Same as before) ---
        zip_in_memory = io.BytesIO(uploaded_zip.getvalue())
        document_texts = {} 
        
        try:
            with zipfile.ZipFile(zip_in_memory, 'r') as zf:
                all_files_in_zip = zf.namelist()
                progress_bar = st.progress(0, text="Reading documents...")
                pdf_files_found = [f for f in all_files_in_zip if f.endswith('.pdf') and not f.startswith('__MACOSX')]
                
                for i, file_name in enumerate(pdf_files_found):
                    progress_bar.progress((i + 1) / len(pdf_files_found), text=f"Reading: {file_name}")
                    with zf.open(file_name) as pdf_file_in_zip:
                        with pdfplumber.open(pdf_file_in_zip) as pdf:
                            full_text = ""
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    full_text += text + "\n\n"
                            document_texts[file_name] = full_text
            
            progress_bar.progress(1.0, text="All documents read!")
            st.success(f"Successfully read {len(document_texts)} PDF document(s).")
            
            # --- Step 2: Combine and "Chunk" the Text ---
            full_document_text = "\n\n--- NEW DOCUMENT --- \n\n".join(document_texts.values())
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
            chunks = text_splitter.split_text(full_document_text)
            docs = [Document(page_content=t) for t in chunks]
            st.info(f"Split {len(full_document_text)} characters into {len(docs)} chunks for analysis.")

            # --- Step 3: Set up the AI and Run Analysis ---
            if st.button("Start Analysis"):
                try:
                    # Initialize the Gemini LLM
                    # *** IMPORTANT: We now get the key from st.secrets ***
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-pro",
                        google_api_key=st.secrets["GOOGLE_API_KEY"], # <-- This is the new, secure way
                        temperature=0.3
                    )

                    prompt_template = """
                    You are a veteran local politician. Analyze the following documents for a city council meeting.
                    Your goal is to provide a concise, 1-page briefing for a busy politician.
                    For the provided text, please generate the following:
                    1.  **Executive Summary:** A very short, high-level summary of the main proposal.
                    2.  **Key Issues & Risks:** What are the potential problems, "gotchas", financial risks, or public concerns hidden in this data?
                    3.  **Relevant Questions to Ask:** What are 3-5 sharp, insightful questions a politician should ask in the meeting based on these risks?
                    
                    Here is the text:
                    {text}
                    
                    YOUR 1-PAGE BRIEFING:
                    """

                    chain = load_summarize_chain(
                        llm,
                        chain_type="map_reduce",
                        map_prompt=st.PromptTemplate(template=prompt_template, input_variables=["text"]),
                        combine_prompt=st.PromptTemplate(template=prompt_template, input_variables=["text"])
                    )

                    with st.spinner("🤖 The AI is reading all documents and thinking... This may take a few minutes..."):
                        summary_output = chain.run(docs)
                    
                    st.success("Analysis Complete!")
                    st.subheader("Your Political Briefing")
                    st.markdown(summary_output)

                except Exception as e:
                    st.error(f"An error occurred during AI analysis: {e}")
                    st.error("Please double-check your GOOGLE_API_KEY in the Streamlit Secrets settings.")
        
        except zipfile.BadZipFile:
            st.error("This does not appear to be a valid ZIP file. Please try again.")

elif password:
    # This shows if they've typed *something* but it's wrong
    st.error("Password incorrect. Please try again.")
else:
    # This is the default state before they type anything
    st.info("Please enter your password to unlock the assistant.")
