import streamlit as st
import zipfile  # Python's built-in library for handling .zip files
import io         # Used to handle the file in memory

# --- Streamlit App Layout ---

st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

# 1. Create the File Uploader
# This 'st.file_uploader' widget is the new UI.
# We set 'type="zip"' to only allow .zip files.
uploaded_zip = st.file_uploader("Upload the ZIP file of meeting documents", type="zip")

# 2. Add logic for what to do AFTER a file is uploaded
if uploaded_zip is not None:
    # 'uploaded_zip' is a file-like object from Streamlit.
    # We use 'io.BytesIO' to treat the uploaded file's bytes as a file
    # that 'zipfile' can read from memory.
    zip_in_memory = io.BytesIO(uploaded_zip.getvalue())
    
    # A list to store the names of the PDFs we find
    pdf_files_found = []
    
    try:
        # Open the ZIP file from memory
        with zipfile.ZipFile(zip_in_memory, 'r') as zf:
            
            # 'zf.namelist()' gives a list of all files in the zip
            all_files_in_zip = zf.namelist()
            
            for file_name in all_files_in_zip:
                # We only care about files that end in .pdf
                # We also ignore common macOS junk files just in case
                if file_name.endswith('.pdf') and not file_name.startswith('__MACOSX'):
                    pdf_files_found.append(file_name)
        
        # 3. Show the results
        if not pdf_files_found:
            st.error("No PDF files were found inside that ZIP.")
        else:
            st.success(f"Found {len(pdf_files_found)} PDF document(s) in the ZIP! 🎉")
            
            with st.expander("Show found document names"):
                for name in pdf_files_found:
                    st.write(name)
            
            # This is where we will add the *next* step:
            st.info("Status: Ready to read and analyze these PDFs.")

    except zipfile.BadZipFile:
        st.error("This does not appear to be a valid ZIP file. Please try again.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    # This is the default message the user sees
    st.info("Please upload the .zip file containing all agenda items.")
