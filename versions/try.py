import streamlit as st
import pandas as pd
import random
import time

# Load your troubleshooting CSV
df = pd.read_csv("troubleshooting.csv")

st.title("🤖 Q Bot")

# Initial greeting message
if "initialized" not in st.session_state:
    with st.chat_message("assistant"):
        st.write("Hi! I'm Q bot, your personal assistant. I'm here to assist you with any query you have regarding Mispa X.")
    #st.session_state.initialized = True

# Typing response generator

def response_generator():
    response = random.choice([
        "Tell me your problem.",
        "How may I assist you?",
        "How can I help you today?",
        "Provide me your issue."
    ])
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = "start"
    st.session_state.selected_eq = None
    st.session_state.selected_error = None
    st.session_state.selected_desc = None

# Show past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input handler
if prompt := st.chat_input("Type your response..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    def bot_reply(message):
        st.session_state.messages.append({"role": "assistant", "content": message})
        with st.chat_message("assistant"):
            st.markdown(message)

    def stream_reply():
        with st.chat_message("assistant"):
            response = st.write_stream(response_generator())
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Bot logic stages
    user_input = prompt
    if st.session_state.stage == "start":
        equipment_options = df["Equipment"].unique()
        st.session_state.equipment_list = list(equipment_options)
        message = "Which equipment are you having issues with?\n\n" + "\n".join([
            f"{i+1}. {e}" for i, e in enumerate(equipment_options)
        ])
        bot_reply(message)
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        try:
            index = int(user_input.strip()) - 1
            st.session_state.selected_eq = st.session_state.equipment_list[index]
            error_options = df[df["Equipment"] == st.session_state.selected_eq]["ERROR"].unique()
            st.session_state.error_list = list(error_options)
            message = f"What issue are you facing with **{st.session_state.selected_eq}**?\n\n" + "\n".join([
                f"{i+1}. {e}" for i, e in enumerate(error_options)
            ])
            bot_reply(message)
            st.session_state.stage = "error"
        except:
            bot_reply("❗ Please enter a valid number for equipment.")

    elif st.session_state.stage == "error":
        try:
            index = int(user_input.strip()) - 1
            st.session_state.selected_error = st.session_state.error_list[index]
            desc_options = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error)
            ]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            message = "Can you describe the problem more specifically?\n\n" + "\n".join([
                f"{i+1}. {d}" for i, d in enumerate(desc_options)
            ])
            bot_reply(message)
            st.session_state.stage = "desc"
        except:
            bot_reply("❗ Please enter a valid number for the issue type.")

    elif st.session_state.stage == "desc":
        try:
            index = int(user_input.strip()) - 1
            st.session_state.selected_desc = st.session_state.desc_list[index]
            steps = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == st.session_state.selected_desc)
            ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

            if not steps:
                bot_reply("⚠️ No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "🔧 Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        except:
            bot_reply("❗ Please enter a valid number for the description.")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input.lower():
            bot_reply("✅ Glad the issue was fixed! Need help with anything else?")
            st.session_state.stage = "end"
        elif "no" in user_input.lower():
            final_solution = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == st.session_state.selected_desc)
            ]["FINAL SOLUTIONS"].dropna().iloc[0]
            bot_reply(f"🔧 Final Solution: {final_solution}")
            st.session_state.stage = "end"
        else:
            bot_reply("❓ Please respond with 'yes' or 'no'.")

    elif st.session_state.stage == "end":
        bot_reply("🔁 If you want to start again, please refresh the page.")
