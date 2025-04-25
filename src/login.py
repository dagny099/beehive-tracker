import streamlit as st

bg_image_url = 'https://raw.githubusercontent.com/dagny099/dagny099.github.io/ff96cc0d1cbc65fbe5a0789eb00d73aff65c4059/assets/images/midjourney/the-mycelium-web/hr-beautiful-forrest-electric-blue-mycelium-yellow-dots-03.png'
favicon_url = "https://raw.githubusercontent.com/dagny099/dagny099.github.io/ff96cc0d1cbc65fbe5a0789eb00d73aff65c4059/assets/images/favicon/android-chrome-256x256.png"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{bg_image_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .login-container {{
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: #333;
    }}
    .login-container img {{
        background-color: rgba(255, 255, 255, 0.15);
        width: 250px;
        height: 250px;
        margin-bottom: 1rem;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}

    .login-container h1 {{
        background-color: rgba(10, 20, 10, 0.75);
        color: #F4F4F1;
        font-size: 2.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 12px;
        border-color: #5CD3FF;
        width: 100%;
    }}

    .login-button button {{
        background-color: #3A5A40;
        color: #F4F4F1;
        font-weight: bold;
        border-radius: 25px;
        padding: 0.6rem 2rem;
        font-size: 1.2rem;
        border: none;
        transition: background-color 0.3s ease;
        margin-top: 1rem;
        cursor: pointer;
    }}

    .login-button button:hover {{
        background-color: #4CAF50;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(f"""
    <div class="login-container">
    <img class="login-container" src={favicon_url} alt="beebarb logo">
    <h1>Welcome to the Hive <br>Photo Metadata Explorer</h1>
    </div>
    """, unsafe_allow_html=True)

login_button = st.button("🐝 Enter Hive", type="tertiary", use_container_width=True)
if login_button:
    st.session_state.logged_in = True  # or whatever your main screen function is
    st.rerun()

