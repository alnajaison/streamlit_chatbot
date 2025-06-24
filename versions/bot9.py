#to handle fuzzy matching for both error and error description inputs with at least 80% similarity, even with extra or missing filler words.

import streamlit as st
import pandas as pd
import random
import time
import difflib

# Load your troubleshooting CSV
df = pd.read_csv("troubleshooting.csv")

st.title(" Q Bot - Troubleshooting Assistant")

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

# Utility to find best fuzzy match
def fuzzy_match(user_input, options, threshold=0.8):
    user_input = user_input.lower()
    options_lower = [opt.lower() for opt in options]
    best_match = difflib.get_close_matches(user_input, options_lower, n=1, cutoff=threshold)
    if best_match:
        return options[options_lower.index(best_match[0])]
    return None

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
        message = "Which equipment are you having issues with?\n\n" + "\n".join(f"- {e}" for e in equipment_options)
        bot_reply(message)
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        matched_eq = fuzzy_match(user_input, st.session_state.equipment_list)
        if matched_eq:
            st.session_state.selected_eq = matched_eq
            error_options = df[df["Equipment"] == matched_eq]["ERROR"].unique()
            st.session_state.error_list = list(error_options)
            desc_options = df[df["Equipment"] == matched_eq]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            combined_list = sorted(set(st.session_state.error_list + st.session_state.desc_list))
            message = f"What issue are you facing with **{matched_eq}**?\n\n" + "\n".join(f"- {item}" for item in combined_list)
            bot_reply(message)
            st.session_state.stage = "error_or_desc"
        else:
            bot_reply(" Please mention a valid equipment name like 'Mispa X'.")

    elif st.session_state.stage == "error_or_desc":
        matched_error = fuzzy_match(user_input, st.session_state.error_list)
        matched_desc = fuzzy_match(user_input, st.session_state.desc_list)

        if matched_error and not matched_desc:
            st.session_state.selected_error = matched_error
            desc_options = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == matched_error)
            ]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            message = "Can you describe the problem more specifically?\n\n" + "\n".join(f"- {d}" for d in desc_options)
            bot_reply(message)
            st.session_state.stage = "desc"

        elif matched_desc:
            st.session_state.selected_desc = matched_desc
            matched_error_from_desc = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR DESCRIPTION"] == matched_desc)
            ]["ERROR"].iloc[0]
            st.session_state.selected_error = matched_error_from_desc
            steps = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == matched_error_from_desc) &
                (df["ERROR DESCRIPTION"] == matched_desc)
            ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

            if not steps:
                bot_reply(" No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "🔧 Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        else:
            bot_reply(" Please mention a valid issue or error description.")

    elif st.session_state.stage == "desc":
        matched_desc = fuzzy_match(user_input, st.session_state.desc_list)
        if matched_desc:
            st.session_state.selected_desc = matched_desc
            steps = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == matched_desc)
            ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

            if not steps:
                bot_reply(" No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "🔧 Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        else:
            bot_reply(" Please describe the issue more clearly.")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input:
            bot_reply(" Glad the issue was fixed! Need help with anything else?")
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
            bot_reply(" Please respond with 'yes' or 'no'.")

    elif st.session_state.stage == "end":
        bot_reply(" If you want to start again, please refresh the page.")
