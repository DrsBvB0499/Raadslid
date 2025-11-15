import streamlit as st
import zipfile  # For reading ZIPs
import io         # For handling files in memory
import pdfplumber # Our new library for reading PDFs

# --- Streamlit App Layout ---

st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

# 1. Create the File Uploader
uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")

# 2. Add logic for what to do AFTER a file is uploaded
if uploaded_zip is not None:
    zip_in_memory = io.BytesIO(uploaded_zip.getvalue())
    
    # We'll store the text of all documents in this dictionary
    # The 'key' will be the filename, the 'value' will be the text
    document_texts = {} 

    try:
        # Open the ZIP file from memory
        with zipfile.ZipFile(zip_in_memory, 'r') as zf:
            
            all_files_in_zip = zf.namelist()
            
            # --- This is the new, important part ---
            
            # Show a status bar as we read the files
            progress_bar = st.progress(0, text="Reading documents...")
            
            pdf_files_found = [f for f in all_files_in_zip if f.endswith('.pdf') and not f.startswith('__MACOSX')]
            
            for i, file_name in enumerate(pdf_files_found):
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(pdf_files_found), text=f"Reading: {file_name}")

                try:
                    # 'zf.open(file_name)' opens the PDF *inside* the zip
                    with zf.open(file_name) as pdf_file_in_zip:
                        
                        # 'pdfplumber.open()' can read this in-memory file
                        with pdfplumber.open(pdf_file_in_zip) as pdf:
                            
                            full_text = "" # A variable to hold all text from this one PDF
                            
                            # Loop through all pages in the PDF
                            for page in pdf.pages:
                                # 'page.extract_text()' gets all text from a page
                                # We add a space just in case text is cut off between pages
                                text = page.extract_text()
                                if text: # Only add if text was found
                                    full_text += text + "\n\n"
                            
                            # Add the combined text to our dictionary
                            document_texts[file_name] = full_text

                except Exception as e:
                    st.warning(f"Could not read {file_name}. Skipping. (Error: {e})")

        # --- End of new, important part ---

        progress_bar.progress(1.0, text="All documents read!")
        
        # 3. Show the results
        if not document_texts:
            st.error("No text could be extracted from the PDF files in that ZIP.")
        else:
            st.success(f"Successfully read text from {len(document_texts)} PDF document(s)! 🎉")
            
            with st.expander("Show extracted text summary"):
                for file_name, text_content in document_texts.items():
                    st.write(f"**{file_name}**")
                    st.info(f"Read {len(text_content)} characters. (Starts with: '{text_content[:100]}...')")
            
            # This is our next goal!
            st.info("Status: Ready to send this text to the AI for analysis.")

    except zipfile.BadZipFile:
        st.error("This does not appear to be a valid ZIP file. Please try again.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    # This is the default message the user sees
    st.info("Please upload the .zip file containing all agenda items.")
