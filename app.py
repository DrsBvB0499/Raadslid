# This is a comment: Lines that start with '#' are notes for humans, not code.

# 1. Import the Streamlit library
# We 'import' it so we can use its commands.
# We also give it a nickname 'st' so we don't have to type 'streamlit' every time.
import streamlit as st

# 2. Add a Title to your app
# 'st.title()' is a command from Streamlit that puts a big title on the webpage.
st.title("Town Hall Assistant")

# 3. Add a Subheader
# 'st.subheader()' is for a slightly smaller title, like a description.
st.subheader("Your personal assistant for analyzing meeting documents.")

# 4. Add a Text Input box
# 'st.text_input()' creates an interactive box where you can type.
# The text "Paste the city meeting URL here:" is the 'label' that tells you what to do.
# We store the *result* (whatever you type) into a variable named 'url_input'.
url_input = st.text_input("Paste the city meeting URL here:")

# 5. Add a Button
# 'st.button()' creates a clickable button.
# We store the *result* (True if clicked, False if not) into a variable named 'analyze_button'.
analyze_button = st.button("Analyze Meeting")

# 6. Add some logic
# This is a simple 'if' statement. It checks if the 'analyze_button' variable is True.
if analyze_button:
    # If the button WAS clicked, do this:
    st.write("Button clicked!") # 'st.write' just prints text to the screen.
    st.write("You entered this URL:", url_input)
else:
    # If the button HAS NOT been clicked yet, do this:
    st.write("Please paste a URL above and click the 'Analyze' button to begin.")