import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- NEW HEADER ---
# This dictionary tells the website we are a "real" browser.
# This is our "disguise" to avoid the 403 Forbidden error.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}

def get_pdf_links(meeting_url):
    """
    Goes to the given URL and scrapes all links that end in '.pdf'.
    """
    pdf_links = []
    
    try:
        # --- MODIFIED LINE ---
        # We add the 'headers=HEADERS' part to our request.
        response = requests.get(meeting_url, headers=HEADERS)
        
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')

        for link_tag in soup.find_all('a'):
            href = link_tag.get('href')

            if href:
                absolute_url = urljoin(meeting_url, href)
                
                # --- A SMALL IMPROVEMENT ---
                # Let's check for '.pdf' anywhere in the link, just in case
                # of links like 'file.pdf?query=123'
                if '.pdf' in absolute_url:
                    pdf_links.append(absolute_url)
        
        # --- A NEW IMPROVEMENT ---
        # Let's remove duplicate links, just in case they appear multiple times.
        unique_pdf_links = list(set(pdf_links))
        return unique_pdf_links

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching the URL: {e}")
        return []

# --- The Streamlit app layout is unchanged ---

st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

url_input = st.text_input("Paste the city meeting URL here:")

analyze_button = st.button("Analyze Meeting")

if analyze_button:
    if not url_input:
        st.warning("Please paste a URL above first.")
    else:
        st.write(f"Starting analysis for: {url_input}")
        
        with st.spinner("Step 1: Searching for document links..."):
            pdf_links_found = get_pdf_links(url_input)
        
        if not pdf_links_found:
            st.error("No PDF links were found on that page. (Or the site is blocking access).")
        else:
            st.success(f"Found {len(pdf_links_found)} PDF document(s)! 🎉")
            
            with st.expander("Show found document links"):
                for link in pdf_links_found:
                    st.write(link)
