# 1. Import all the libraries we need
import streamlit as st
import requests  # To download the webpage
from bs4 import BeautifulSoup  # To parse the webpage's HTML
from urllib.parse import urljoin  # To fix relative links (e.g., /file.pdf -> https://city.gov/file.pdf)

# 2. Define the new scraper function
# We create a separate 'function' for this to keep our code organized.
def get_pdf_links(meeting_url):
    """
    Goes to the given URL and scrapes all links that end in '.pdf'.
    """
    pdf_links = [] # A list to store the links we find
    
    try:
        # 'requests.get' downloads the HTML of the page
        response = requests.get(meeting_url)
        
        # 'raise_for_status()' will stop the code if the URL is bad (e.g., 404 Not Found)
        response.raise_for_status() 

        # 'BeautifulSoup' takes the messy HTML and makes it easy to search
        soup = BeautifulSoup(response.text, 'html.parser')

        # 'soup.find_all('a')' finds EVERY link tag (<a>) on the page
        for link_tag in soup.find_all('a'):
            
            # 'link_tag.get('href')' gets the actual URL from the link
            href = link_tag.get('href')

            if href: # Make sure the link is not empty
                # We use 'urljoin' to turn relative links (like "/docs/plan.pdf")
                # into absolute links (like "https://city.gov/docs/plan.pdf")
                absolute_url = urljoin(meeting_url, href)
                
                # Our goal: only find PDF documents!
                if absolute_url.endswith('.pdf'):
                    pdf_links.append(absolute_url)
        
        return pdf_links

    except requests.exceptions.RequestException as e:
        # If anything goes wrong (bad URL, no connection), we'll tell the user.
        st.error(f"Error fetching the URL: {e}")
        return [] # Return an empty list

# --- From here, it's our original Streamlit app layout ---

# 3. Add a Title to your app
st.title("Town Hall Assistant")
st.subheader("Your personal assistant for analyzing meeting documents.")

# 4. Add a Text Input box
url_input = st.text_input("Paste the city meeting URL here:")

# 5. Add a Button
analyze_button = st.button("Analyze Meeting")

# 6. Update our logic!
if analyze_button:
    # First, check if the user actually provided a URL
    if not url_input:
        st.warning("Please paste a URL above first.")
    else:
        st.write(f"Starting analysis for: {url_input}")
        
        # This is where we call our new function!
        # We'll show a "spinner" so the user knows it's working.
        with st.spinner("Step 1: Searching for document links..."):
            pdf_links_found = get_pdf_links(url_input)
        
        # Now, show the results
        if not pdf_links_found:
            st.error("No PDF links were found on that page.")
        else:
            st.success(f"Found {len(pdf_links_found)} PDF document(s)! 🎉")
            
            # 'st.expander' makes a nice collapsible box
            with st.expander("Show found document links"):
                for link in pdf_links_found:
                    st.write(link)
