import streamlit as st
from langgraph_backend import chatbot,retrieve_all_threads,get_all_titles,save_title
from langchain_core.messages import HumanMessage, AIMessage
import uuid


# functions 

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_titles'][thread_id] = "New Chat"
        save_title(thread_id, "New Chat")


def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages',[])

# session setup

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_titles' not in st.session_state:
    st.session_state['thread_titles'] = get_all_titles()

add_thread(st.session_state['thread_id'])

# user input 

user_input = st.chat_input('Ask anything')

if user_input:
    thread_id = st.session_state['thread_id']
    if st.session_state['thread_titles'].get(thread_id, "New Chat") == "New Chat":
        title = user_input[:25]
        st.session_state['thread_titles'][thread_id] = title
        save_title(thread_id, title)

    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input}
    )

# sidebar ui

st.sidebar.title('Chatbot')

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header('Your chats')

for thread_id in st.session_state['chat_threads'][::-1]:
    title = st.session_state['thread_titles'].get(thread_id, "Chat")
    if st.sidebar.button(title, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages

# main ui

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


if user_input:

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        def ai_only_stream():
            for message_chunk ,metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,stream_mode="messages"):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

