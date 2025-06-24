import streamlit as st
import pandas as pd
import random
import time

# Load your troubleshooting CSV
df = pd.read_csv("troubleshooting.csv")

st.title("🤖 Q Bot - Troubleshooting Assistant")

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

    user_input = prompt.lower().strip()

    if st.session_state.stage == "start":
        equipment_options = df["Equipment"].unique()
        st.session_state.equipment_list = list(equipment_options)
        message = "Which equipment are you having issues with?\n\n" + "\n".join([f"- {e}" for e in equipment_options])
        bot_reply(message)
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        matched_eq = next((e for e in st.session_state.equipment_list if e.lower() in user_input), None)
        if matched_eq:
            st.session_state.selected_eq = matched_eq
            error_options = df[df["Equipment"] == matched_eq]["ERROR"].unique()
            st.session_state.error_list = list(error_options)
            message = f"What issue are you facing with **{matched_eq}**?\n\n" #+ "\n".join([f"- {e}" for e in error_options])
            bot_reply(message)
            st.session_state.stage = "error"
        else:
            bot_reply("❗ Please mention a valid equipment name like 'Mispa X'.")

    elif st.session_state.stage == "error":
        matched_error = next((e for e in st.session_state.error_list if e.lower() in user_input), None)
        if matched_error:
            st.session_state.selected_error = matched_error
            desc_options = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == matched_error)
            ]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            message = "Can you describe the problem more specifically?\n\n" + "\n".join([f"- {d}" for d in desc_options])
            bot_reply(message)
            st.session_state.stage = "desc"
        else:
            bot_reply("❗ Please mention a valid error type.")

    elif st.session_state.stage == "desc":
        matched_desc = next((d for d in st.session_state.desc_list if d.lower() in user_input), None)
        if matched_desc:
            st.session_state.selected_desc = matched_desc
            steps = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == matched_desc)
            ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

            if not steps:
                bot_reply("⚠️ No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "🔧 Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        else:
            bot_reply("❗ Please describe the issue more clearly.")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input:
            bot_reply("✅ Glad the issue was fixed! Need help with anything else?")
            st.session_state.stage = "end"
        elif "no" in user_input:
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
