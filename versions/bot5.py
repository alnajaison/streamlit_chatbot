import streamlit as st
import random
import time

st.title("Q bot")

with st.chat_message("assistant"):
    st.write("Hi! I'm Q bot, your personal assistant. I'm here to assist you with any query you have regarding Mispa X.")

#streamed response emulator
def response_generator():
    response=random.choice(
        [
            "Tell me your problem.", "How may I assist you?", "How can I help you today?","Provide me your issue."
        ]
    )
    #for the typing effect
    for word in response.split():
        yield word + " "
        time.sleep(0.05) #a delay btw each word

#initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages=[]

#display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message['content'])

#accept user input
if prompt:=st.chat_input("Type in here ..."):

    #add user message to chat history
    st.session_state.messages.append({"role":'user', "content":prompt})
    #display user message in chat conatiner
    with st.chat_message("user"):
        st.markdown(prompt)
    
    #display assistant response in chat message container
    with st.chat_message("assistant"):
        response=st.write_stream(response_generator())
    #addd assistant response to chat history
    st.session_state.messages.append({"role":"assistant", "content":response})