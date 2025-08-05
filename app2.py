import streamlit as st
import streamlit.components.v1 as components

st.title("Retrieve userID from Local Storage")

# Custom JavaScript to get userID and send it to Streamlit
components.html(
    """
    <script>
        // Wait for the DOM to load
        document.addEventListener("DOMContentLoaded", function () {
            const userID = localStorage.getItem("userID");

            // Send it to Streamlit using an iframe hack
            const streamlitReceiver = window.parent;
            if (streamlitReceiver) {
                streamlitReceiver.postMessage({ type: "userID", value: userID }, "*");
            }
        });
    </script>

    <iframe id="receiver" style="display:none;"></iframe>
    """,
    height=0,  # Hide the component
)

# Placeholder to display userID
user_id = st.empty()

# Read the message from the frontend using streamlit's experimental_get_query_params (indirect way)
# Use a custom receiver
import streamlit_javascript as st_js  # requires st_javascript

# If you don’t want to use external libs, we can alternatively use a hack with session state + JS listener

# But for a clean approach:
# Install: pip install streamlit-javascript
from streamlit_javascript import st_javascript

userID = st_javascript("localStorage.getItem('userID');")
if userID:
    st.success(f"userID from localStorage: {userID}")
else:
    st.warning("userID not found in localStorage.")