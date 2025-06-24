#typing effect added for all the responses

import streamlit as st
import pandas as pd
import random
import time
import difflib

# Load your troubleshooting CSV
df = pd.read_csv("troubleshooting.csv")

st.title("@createdbyalna")

# Initial greeting message
if "initialized" not in st.session_state:
    with st.chat_message("assistant"):
        st.write_stream((word + " " for word in "Hi! I'm Q bot, your personal assistant. I'm here to assist you with any query you have regarding Mispa X.".split()))
    #st.session_state.initialized = True

# Typing response generator
def stream_response(message):
    for line in message.split("\n"):
        line = line.strip()
        if line.startswith("-"):
            yield "- "
            for word in line[1:].strip().split():
                yield word + " "
                time.sleep(0.05)
            yield "\n"
        else:
            for word in line.split():
                yield word + " "
                time.sleep(0.05)
            yield "\n"

def stream_bot_reply(message):
    with st.chat_message("assistant"):
        st.write_stream(stream_response(message))
    st.session_state.messages.append({"role": "assistant", "content": message})

# Utility to find best fuzzy match
from difflib import SequenceMatcher

def best_fuzzy_match(user_input, options, threshold=0.6):
    user_input = user_input.lower()
    best_match = None
    best_score = 0
    for option in options:
        ratio = SequenceMatcher(None, user_input, option.lower()).ratio()
        if ratio > best_score:
            best_score = ratio
            best_match = option
    if best_score >= threshold:
        return best_match
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

    user_input = prompt.lower().strip()

    if st.session_state.stage == "start":
        equipment_options = df["Equipment"].unique()
        st.session_state.equipment_list = list(equipment_options)
        message = "Which equipment are you having issues with?\n\n" + "\n".join(f"- {e}" for e in equipment_options)
        stream_bot_reply(message)
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        matched_eq = best_fuzzy_match(user_input, st.session_state.equipment_list)
        if matched_eq:
            st.session_state.selected_eq = matched_eq
            error_options = df[df["Equipment"] == matched_eq]["ERROR"].unique()
            st.session_state.error_list = list(error_options)
            desc_options = df[df["Equipment"] == matched_eq]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            combined_list = sorted(set(st.session_state.error_list + st.session_state.desc_list))
            message = f"What issue are you facing with **{matched_eq}**?\n\n" #+ "\n".join(f"- {item}" for item in combined_list)
            stream_bot_reply(message)
            st.session_state.stage = "error_or_desc"
        else:
            stream_bot_reply("Please mention a valid equipment name like 'Mispa X'.")

    elif st.session_state.stage == "error_or_desc":
        combined_list = st.session_state.error_list + st.session_state.desc_list
        matched_text = best_fuzzy_match(user_input, combined_list)

        if matched_text:
            if matched_text in st.session_state.error_list:
                st.session_state.selected_error = matched_text
                desc_options = df[
                    (df["Equipment"] == st.session_state.selected_eq) &
                    (df["ERROR"] == matched_text)
                ]["ERROR DESCRIPTION"].unique()
                st.session_state.desc_list = list(desc_options)
                message = "Can you describe the problem more specifically?\n\n" + "\n".join(f"- {d}" for d in desc_options)
                stream_bot_reply(message)
                st.session_state.stage = "desc"

            elif matched_text in st.session_state.desc_list:
                st.session_state.selected_desc = matched_text
                matched_error_from_desc = df[
                    (df["Equipment"] == st.session_state.selected_eq) &
                    (df["ERROR DESCRIPTION"] == matched_text)
                ]["ERROR"].iloc[0]
                st.session_state.selected_error = matched_error_from_desc
                steps = df[
                    (df["Equipment"] == st.session_state.selected_eq) &
                    (df["ERROR"] == matched_error_from_desc) &
                    (df["ERROR DESCRIPTION"] == matched_text)
                ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

                if not steps:
                    stream_bot_reply("No troubleshooting steps found for this issue.")
                    st.session_state.stage = "end"
                else:
                    reply = "Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                    stream_bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                    st.session_state.stage = "troubleshoot"
        else:
            stream_bot_reply("Please mention a valid issue or error description.")

    elif st.session_state.stage == "desc":
        matched_desc = best_fuzzy_match(user_input, st.session_state.desc_list)
        if matched_desc:
            st.session_state.selected_desc = matched_desc
            steps = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == matched_desc)
            ]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()

            if not steps:
                stream_bot_reply("No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                stream_bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        else:
            stream_bot_reply("Please describe the issue more clearly.")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input:
            stream_bot_reply("Glad the issue was fixed! Need help with anything else?")
            st.session_state.stage = "end"
        elif "no" in user_input:
            final_solution = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error) &
                (df["ERROR DESCRIPTION"] == st.session_state.selected_desc)
            ]["FINAL SOLUTIONS"].dropna().iloc[0]
            stream_bot_reply(f"Final Solution: {final_solution}")
            st.session_state.stage = "end"
        else:
            stream_bot_reply("Please respond with 'yes' or 'no'.")

    elif st.session_state.stage == "end":
        stream_bot_reply("If you want to start again, please refresh the page.")