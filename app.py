import streamlit as st
from google import genai
from ecologits import EcoLogits
from groq import Groq

# Initialize EcoLogits
EcoLogits.init(providers=["google_genai"])

# Load API keys
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🌱 Green AI Chat Router (Gemini + Groq)")

# Sidebar
st.sidebar.title("Model Settings")
st.sidebar.write("Compare energy usage, speed, and performance.")

selected_model = st.sidebar.selectbox(
    "Choose AI Model:",
    [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "groq-llama",
        "groq-mixtral"
    ]
)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What would you like to ask?"):

    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Prepare Gemini history
    gemini_history = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # Prepare Groq history
    groq_messages = []
    for msg in st.session_state.messages:
        groq_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Assistant response
    with st.chat_message("assistant"):

        try:
            # ================= GEMINI =================
            if "gemini" in selected_model:

                response = client.models.generate_content(
                    model=selected_model,
                    contents=gemini_history
                )

                answer = response.text if hasattr(response, "text") and response.text else response.candidates[0].content.parts[0].text
                st.markdown(answer)

            # ================= GROQ =================
            elif "groq" in selected_model:

                model_name = "llama-3.3-70b" if "llama" in selected_model else "mixtral-8x7b-32768"

                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=groq_messages
                )

                answer = response.choices[0].message.content
                st.markdown(answer)

        except Exception as e:

            # 🔄 Auto fallback for Gemini Pro
            if selected_model == "gemini-2.5-pro":
                st.info("🔄 Switching to eco-friendly model (flash-lite)...")

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=gemini_history
                    )

                    answer = response.text if hasattr(response, "text") and response.text else response.candidates[0].content.parts[0].text
                    st.markdown(answer)

                    st.success("🌱 Eco Mode Active")

                except:
                    st.error("🚫 Fallback also failed.")
                    answer = "⚠️ Unable to generate response."
                    st.markdown(answer)

            else:
                st.error("🚫 Model error occurred.")
                answer = "⚠️ Unable to generate response."
                st.markdown(answer)

        # ================= ECOLOGITS =================
        try:
            if "gemini" in selected_model:
                energy_wh = response.impacts.energy.value * 1000
                carbon_g = response.impacts.gwp.value * 1000

                st.divider()
                st.write("📊 **Impact Metrics:**")

                col1, col2 = st.columns(2)
                col1.metric("⚡ Energy Used", f"{energy_wh:.4f} Wh")
                col2.metric("🌍 Carbon Footprint", f"{carbon_g:.6f} gCO₂")

            else:
                st.info("⚡ Groq Mode: Ultra-fast responses (no energy data yet)")

        except:
            st.warning("⚠️ Impact data not available.")

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })