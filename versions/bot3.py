import streamlit as st
import pandas as pd

# Load your troubleshooting CSV
df = pd.read_csv("troubleshooting.csv")

# --- Initialize session state ---
if "stage" not in st.session_state:
    st.session_state.stage = "start"
    st.session_state.chat_history = []
    st.session_state.selected_eq = None
    st.session_state.selected_error = None
    st.session_state.selected_desc = None

# --- Chat message display ---
st.title(" Troubleshooting Chat Assistant")
for role, msg in st.session_state.chat_history:
    with st.chat_message("assistant" if role == "bot" else "user"):
        st.markdown(msg)

def bot_reply(message):
    st.session_state.chat_history.append(("bot", message))

def user_reply(message):
    st.session_state.chat_history.append(("user", message))

# --- Process logic per stage ---
def process_input(user_input):
    user_reply(user_input)

    # Stage 1: Equipment selection
    if st.session_state.stage == "start":
        equipment_options = df["Equipment"].unique()
        st.session_state.equipment_list = list(equipment_options)
        bot_reply("Which equipment are you having issues with?\n\n" +
                  "\n".join([f"{i+1}. {e}" for i, e in enumerate(equipment_options)]))
        st.session_state.stage = "equipment"

    elif st.session_state.stage == "equipment":
        try:
            index = int(user_input.strip()) - 1
            st.session_state.selected_eq = st.session_state.equipment_list[index]
            error_options = df[df["Equipment"] == st.session_state.selected_eq]["ERROR"].unique()
            st.session_state.error_list = list(error_options)
            bot_reply(f"What issue are you facing with **{st.session_state.selected_eq}**?\n\n" +
                      "\n".join([f"{i+1}. {e}" for i, e in enumerate(error_options)]))
            st.session_state.stage = "error"
        except:
            bot_reply(" Please enter a valid number for equipment.")

    elif st.session_state.stage == "error":
        try:
            index = int(user_input.strip()) - 1
            st.session_state.selected_error = st.session_state.error_list[index]
            desc_options = df[
                (df["Equipment"] == st.session_state.selected_eq) &
                (df["ERROR"] == st.session_state.selected_error)
            ]["ERROR DESCRIPTION"].unique()
            st.session_state.desc_list = list(desc_options)
            bot_reply("Can you describe the problem more specifically?\n\n" +
                      "\n".join([f"{i+1}. {d}" for i, d in enumerate(desc_options)]))
            st.session_state.stage = "desc"
        except:
            bot_reply(" Please enter a valid number for the issue type.")

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
                bot_reply(" No troubleshooting steps found for this issue.")
                st.session_state.stage = "end"
            else:
                reply = "🔧 Try these steps:\n" + "\n".join([f"- {s}" for s in steps])
                bot_reply(reply + "\n\nDid this fix the issue? (yes/no)")
                st.session_state.stage = "troubleshoot"
        except:
            bot_reply(" Please enter a valid number for the description.")

    elif st.session_state.stage == "troubleshoot":
        if "yes" in user_input.lower():
            bot_reply(" Glad the issue was fixed! Need help with anything else?")
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
            bot_reply(" Please respond with 'yes' or 'no'.")

    elif st.session_state.stage == "end":
        bot_reply(" If you want to start again, please refresh the page.")

# --- Chat input ---
user_input = st.chat_input("Type your response...")
if user_input:
    process_input(user_input)
