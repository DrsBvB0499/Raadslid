import streamlit as st
import zipfile
import io
import pdfplumber

# --- NEW, SIMPLER AI IMPORT ---
import google.generativeai as genai


def analyze_text(api_key, text_to_analyze):
    """
    Analyzes the text using the Google AI library directly,
    without LangChain.
    """
    try:
        # Configure the API key
        genai.configure(api_key=api_key)

        # Create the model
        model = genai.GenerativeModel('gemini-2.5-pro')

        # This is your specific prompt
        prompt = """
        You are a veteran local politician. Analyze the following documents for a city council meeting.
        Your goal is to provide a concise, 1-page briefing for a busy politician.

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

# 1. Ask for the simple app password
password = st.text_input("Enter your app password:", type="password")

# 2. Check password
if password == st.secrets["APP_PASSWORD"]:
    st.success("Login successful!")

    uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")

    if uploaded_zip is not None:
        zip_in_memory = io.BytesIO(uploaded_zip.getvalue())
        document_texts = {} 

        try:
            # --- Step 1: Read the PDF Text (Unchanged) ---
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

            # --- Step 2: Combine Text (Simpler) ---
            full_document_text = "\n\n--- NEW DOCUMENT: {name} --- \n\n".join(
                f"{name}\n{text}" for name, text in document_texts.items()
            )

            if st.button("Start Analysis"):
                # --- Step 3: Run AI Analysis (New, Simpler) ---
                with st.spinner("🤖 The AI is reading all documents and thinking... This may take a minute..."):

                    summary_output = analyze_text(st.secrets["GOOGLE_API_KEY"], full_document_text)

                    if summary_output:
                        st.success("Analysis Complete!")
                        st.subheader("Your Political Briefing")
                        st.markdown(summary_output)
                    else:
                        st.error("Analysis failed. Please check the API key in your secrets.")

        except zipfile.BadZipFile:
            st.error("This does not appear to be a valid ZIP file. Please try again.")

elif password:
    st.error("Password incorrect. Please try again.")
else:
    st.info("Please enter your password to unlock the assistant.")



