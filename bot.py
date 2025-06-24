#to prevent your chatbot from responding to irrelevant or unrelated input
#18

import streamlit as st
import pandas as pd
import time
import os
import subprocess
import speech_recognition as sr
from difflib import SequenceMatcher
from streamlit_mic_recorder import mic_recorder

# Load data
df = pd.read_csv("troubleshooting.csv")

st.title("@createdbyalna")

# Initialize session
if "initialized" not in st.session_state:
    intro_msg = "Hi! I'm Q bot, your personal assistant. I'm here to assist you with any query you have regarding Mispa X."
    st.session_state.messages = [{"role": "assistant", "content": intro_msg}]
    st.session_state.initialized = True
    st.session_state.stage = "start"
    st.session_state.selected_eq = None
    st.session_state.selected_error = None
    st.session_state.selected_desc = None

# Show message history
for msg in st.session_state.messages:
    avatar = "👩‍🦰" if msg["role"] == "user" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Response streaming
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

# Similarity match with threshold
def best_match(user_input, options, threshold=0.5):
    best = None
    best_score = 0
    for opt in options:
        score = SequenceMatcher(None, user_input.lower(), str(opt).lower()).ratio()
        if score > best_score:
            best = opt
            best_score = score
    return best if best_score >= threshold else None

# Mic input
mic_key = f"mic_{len(st.session_state.messages)}"
voice_input = mic_recorder(start_prompt="🎙️ Speak", stop_prompt="🛑 Stop", just_once=True, key=mic_key)
text_input = st.chat_input("Type your message...")

prompt = None

# Process voice input
if voice_input and isinstance(voice_input, dict) and "bytes" in voice_input:
    try:
        with open("temp.webm", "wb") as f:
            f.write(voice_input["bytes"])
        subprocess.run(["ffmpeg", "-y", "-i", "temp.webm", "temp.wav"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        recognizer = sr.Recognizer()
        with sr.AudioFile("temp.wav") as source:
            audio = recognizer.record(source)
        try:
            prompt = recognizer.recognize_google(audio)
            if not prompt.strip():
                raise sr.UnknownValueError()
        except sr.UnknownValueError:
            st.warning("🎤 Could not understand the audio. Please try again.")
            prompt = None
        except sr.RequestError as e:
            st.error(f"🎤 Speech API error: {e}")
            prompt = None
        os.remove("temp.webm")
        os.remove("temp.wav")
    except Exception as e:
        st.error(f"🎤 Voice processing failed: {e}")
        prompt = None
    finally:
        st.session_state.pop(mic_key, None)

# Text input
if text_input:
    prompt = text_input

# Process input
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👩‍🦰"):
        st.markdown(prompt)
    user_input = prompt.lower()

    if st.session_state.stage == "start":
        eq_list = df["Equipment"].dropna().unique()
        st.session_state.eq_list = eq_list
        message = "Which equipment are you having issues with?\n\n" + "\n".join(f"- {e}" for e in eq_list)
        stream_bot_reply(message)
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        eq = best_match(user_input, st.session_state.eq_list)
        if eq:
            st.session_state.selected_eq = eq
            subset = df[df["Equipment"] == eq]
            st.session_state.error_list = subset["ERROR"].dropna().unique()
            st.session_state.desc_list = subset["ERROR DESCRIPTION"].dropna().unique()
            stream_bot_reply(f"What issue are you facing with **{eq}**?")
            st.session_state.stage = "issue"
        else:
            stream_bot_reply("** I didn’t get you. Please mention a valid equipment name. **")

    elif st.session_state.stage == "issue":
        err_match = best_match(user_input, st.session_state.error_list)
        desc_match = best_match(user_input, st.session_state.desc_list)

        if err_match:
            st.session_state.selected_error = err_match
            descs = df[(df["Equipment"] == st.session_state.selected_eq) &
                       (df["ERROR"] == err_match)]["ERROR DESCRIPTION"].dropna().unique()
            st.session_state.desc_list = descs
            message = "Please describe the issue in more detail:\n" + "\n".join(f"- {d}" for d in descs)
            stream_bot_reply(message)
            st.session_state.stage = "desc"
        elif desc_match:
            st.session_state.selected_desc = desc_match
            err = df[(df["Equipment"] == st.session_state.selected_eq) &
                     (df["ERROR DESCRIPTION"] == desc_match)]["ERROR"].iloc[0]
            st.session_state.selected_error = err
            steps = df[(df["Equipment"] == st.session_state.selected_eq) &
                       (df["ERROR"] == err) &
                       (df["ERROR DESCRIPTION"] == desc_match)]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()
            if steps:
                message = "Try these steps:\n" + "\n".join(f"- {s}" for s in steps) + "\n\nDid it work? (yes/no)"
                stream_bot_reply(message)
                st.session_state.stage = "troubleshoot"
            else:
                stream_bot_reply(" No troubleshooting steps found.")
                st.session_state.stage = "end"
        else:
            stream_bot_reply("** I didn’t get you. Please describe the issue more clearly. **")

    elif st.session_state.stage == "desc":
        desc = best_match(user_input, st.session_state.desc_list)
        if desc:
            st.session_state.selected_desc = desc
            steps = df[(df["Equipment"] == st.session_state.selected_eq) &
                       (df["ERROR"] == st.session_state.selected_error) &
                       (df["ERROR DESCRIPTION"] == desc)]["ACTION POINTS / TROUBLE SHOOTING"].dropna().tolist()
            if steps:
                message = "Try these steps:\n" + "\n".join(f"- {s}" for s in steps) + "\n\nDid it work? (yes/no)"
                stream_bot_reply(message)
                st.session_state.stage = "troubleshoot"
            else:
                stream_bot_reply(" No troubleshooting steps found.")
                st.session_state.stage = "end"
        else:
            stream_bot_reply("** I didn’t get you. Please select a valid issue description. **")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input:
            stream_bot_reply("✅ Glad the issue was fixed! Need help with anything else?")
            st.session_state.stage = "end"
        elif "no" in user_input:
            sol = df[(df["Equipment"] == st.session_state.selected_eq) &
                     (df["ERROR"] == st.session_state.selected_error) &
                     (df["ERROR DESCRIPTION"] == st.session_state.selected_desc)]["FINAL SOLUTIONS"].dropna().iloc[0]
            stream_bot_reply(f" Final Solution:\n{sol}")
            st.session_state.stage = "end"
        else:
            stream_bot_reply("Please reply with 'yes' or 'no'.")

    elif st.session_state.stage == "end":
        stream_bot_reply("🔁 To troubleshoot something else, just type or speak again.")
        st.session_state.stage = "start"
