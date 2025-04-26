# --------------------------------------------------------------------------
# run_tracker.py
# Should be located in root directory of the Beehive Metadata Tracker project
# git://github.com/dagny099/hivetracker
# --------------------------------------------------------------------------
import streamlit as st
import os

# Create necessary directories if they don't exist
os.makedirs("data/uploads", exist_ok=True)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Set page configuration
st.set_page_config(
    page_title="Hive Photo Metadata Tracker",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded"
)

def logout():
    st.subheader("👋🏽 You're now logged out")
    if st.button("Reset"):
        st.session_state.logged_in = False
        st.rerun()

# Set up the page with MULTIPAGE NAVIGATION
login_page = st.Page("src/login.py", title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

dashboard = st.Page("src/app.py", title="Dashboard", icon=":material/dashboard:", default=True)
calendar = st.Page("src/calendar_view.py", title="Calendar", icon=":material/calendar_month:")
gallery = st.Page("src/gallery_view.py", title="Photo Gallery", icon=":material/photo_library:")

# Add more pages as they become available
# trends = st.Page("src/trends.py", title="Trends", icon=":material/data_exploration:")
# settings = st.Page("src/settings.py", title="Settings", icon=":material/settings:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Hive Tracker": [dashboard],
            "Views": [calendar, gallery],
            # "Analytics": [trends],
            "Account": [logout_page],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()

# URLS
        # value="https://drive.google.com/uc?export=view&id=1aP-MjQ_wGG7RFyO0skn_cu7A2r7bh4iA",  #2024
        # value="https://drive.google.com/uc?export=view&id=1iGytEfHMEXV2fNqI3z6aE49baoOt8W_B"  #2020
        # value="https://drive.google.com/uc?export=view&id=1qbvRpDnseTcq1fd69wKkTUl5VDZMO4Vc"  #2023
        # value="https://drive.google.com/uc?export=view&id=1ikdU2FT2L28hK9xH3Cy0R5BW-atAVd9l"  #2023, same day
        # value="https://drive.google.com/uc?export=view&id=1KpMn4k3FRLeMzca8TJjblsq89sgQSSwN"  #2023, different day
