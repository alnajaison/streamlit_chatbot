import streamlit as st
#ECHOBOT - bot that mirrors your input

st.title("Q bot")

#initialise chat history
if "messages" not in st.session_state:
    st.session_state.messages=[]

#display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#react to user input
if prompt :=st.chat_input("Type in here ..."):
    
    #display user message in chat message conatiner
    with st.chat_message("user", avatar="👩‍🦰"):
        st.markdown(prompt)
    #add user message to chat history
    st.session_state.messages.append({"role":"user","content":prompt})

    response=f"Echo: {prompt}"
    #display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    #add assistant response to chat history
    st.session_state.messages.append({"role":"assistant", "content":response})