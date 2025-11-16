# core/file_processing.py
import streamlit as st
from PyPDF2 import PdfReader
import zipfile
import io

def process_uploaded_files(uploaded_files):
    """
    Reads all uploaded files (PDFs and ZIPs) and extracts text.
    Adds clear source citations (filename + page number) for all text.
    """
    full_text = ""
    if not uploaded_files:
        return ""
        
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        st.write(f"Verwerken van: {filename}...") 
        
        try:
            # Must reset buffer position for reading
            uploaded_file.seek(0)
            if uploaded_file.type == "application/pdf":
                reader = PdfReader(uploaded_file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n\n--- START BRON: {filename} (Pagina {page_num + 1}) ---\n"
                        full_text += page_text
                        full_text += f"\n--- EINDE BRON: {filename} (Pagina {page_num + 1}) ---\n"

            elif uploaded_file.type == "application/zip":
                with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zf:
                    for internal_file_info in zf.infolist():
                        if internal_file_info.is_dir() or not internal_file_info.filename.lower().endswith('.pdf'):
                            continue
                        
                        internal_filename = internal_file_info.filename
                        st.write(f"  ... Verwerken (in ZIP): {internal_filename}") 
                        
                        with zf.open(internal_file_info) as pdf_file_in_zip:
                            pdf_stream = io.BytesIO(pdf_file_in_zip.read())
                            try:
                                reader = PdfReader(pdf_stream)
                                for page_num, page in enumerate(reader.pages):
                                    page_text = page.extract_text()
                                    if page_text:
                                        citation_name = f"{filename} -> {internal_filename}"
                                        full_text += f"\n\n--- START BRON: {citation_name} (Pagina {page_num + 1}) ---\n"
                                        full_text += page_text
                                        full_text += f"\n--- EINDE BRON: {citation_name} (Pagina {page_num + 1}) ---\n"
                            except Exception as e_pdf:
                                st.warning(f"Kon {internal_filename} in de ZIP niet lezen: {e_pdf}") 
                                
        except Exception as e_file:
            st.error(f"Fout bij het lezen van {filename}: {e_file}") 
            
    st.write("Alle documenten zijn verwerkt.") 
    return full_text
