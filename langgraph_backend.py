from langgraph.graph import StateGraph ,START ,END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = ChatMistralAI(model="mistral-small-latest")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]

def chat_node(state:ChatState):
    messages =state['messages']
    response =llm.invoke(messages)
    return {"messages" :[response]}

conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_titles (
    thread_id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id FROM chat_titles ORDER BY created_at ASC")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def save_title(thread_id, title):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_titles (thread_id, title, created_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(thread_id) DO UPDATE SET title = excluded.title
    """, (str(thread_id), title))
    conn.commit()


def get_all_titles():
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, title FROM chat_titles")
    return {row[0]: row[1] for row in cursor.fetchall()}

