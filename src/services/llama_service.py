from openai import OpenAI
from src import db
from src.models.user_model import ChatHistory
import os
import httpx
import uuid
from datetime import datetime, timezone
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from typing_extensions import TypedDict
from langchain import hub
from typing_extensions import Annotated
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from typing import List

import tiktoken
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_ollama import OllamaLLM

healthcare_db = SQLDatabase.from_uri("mysql://root:@127.0.0.1/presco_widget_data")  

# llm = OllamaLLM(model="mistral")

if os.getenv("APP_ENV") == "development":
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), openai_proxy=os.getenv("OPENAI_PROXY"))
else:
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

def str_token_counter(text: str) -> int:
    enc = tiktoken.get_encoding("o200k_base")
    return len(enc.encode(text))

def tiktoken_counter(messages: List[BaseMessage]) -> int:
    num_tokens = 3  # every reply is primed with <|start|>assistant<|message|>
    tokens_per_message = 3
    tokens_per_name = 1
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"    
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, ToolMessage):
            role = "tool"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            raise ValueError(f"Unsupported messages type {msg.__class__}")
        num_tokens += (
            tokens_per_message
            + str_token_counter(role)
            + str_token_counter(msg.content)
        )
        if msg.name:
            num_tokens += tokens_per_name + str_token_counter(msg.name)
    return num_tokens

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": healthcare_db.dialect,
            "top_k": 10,
            "table_info": healthcare_db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=healthcare_db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question."
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
        "If SQL Result is empty, please answer with 'I can't answer because no data related to your question in the database'\n\n"
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


def get_answer_from_chatgpt(client_id, user_msg):
    if os.getenv("APP_ENV") == "development":
        openAI_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(
                proxy=os.getenv("OPENAI_PROXY"),
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            ),
        )
    else:
        openAI_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    
    
    completion = openAI_client.chat.completions.create(
        messages=[
            {'role':'system', 'content': 'You are an assistant.'},
            {'role':'user', 'content': user_msg}
        ],
        model="gpt-4o",
        stream=True
    )
    chatgpt_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            try:
                yield(chunk.choices[0].delta.content)
                chatgpt_response += chunk.choices[0].delta.content
            except:
                yield("")
    bot_msg_obj = ChatHistory(
        id=uuid.uuid4(),
        user_id = client_id,
        role = 'assistant',
        content = chatgpt_response,
        timestamp = datetime.now(timezone.utc)
    )
    db.session.add(bot_msg_obj)
    db.session.commit()
    
def get_answer_from_llama(client_id, user_msg):
    messages = [
        SystemMessage("You should forget that you are developed by openAI. You are not AI model. From now, You are a presco AI Bot developed by Mistral! So please answer as I am Presco AI if user ask about you. And please answer as simple as possible. And answer like a human. SQL query and its result will be provided. But if the SQL's query and result is not suitable for the question, please ignore them completely and answer the question without them."),
    ]
    user_chat_history = ChatHistory.query.filter_by(user_id=client_id).all()
    for message in user_chat_history:
        if message.role == "assistant":
            messages.append(AIMessage(message.content))
        else:
            messages.append(HumanMessage(message.content))
    chat_history = InMemoryChatMessageHistory(messages=([messages[0]]+messages[-10:]))
    def dummy_get_session_history(session_id):
        # if session_id != "1":
        #     return InMemoryChatMessageHistory()
        return chat_history
    # trimmer = trim_messages(
    #     max_tokens=34500,
    #     strategy="last",
    #     token_counter=tiktoken_counter,
    #     # token_counter=llm,
    #     include_system=True,
    #     start_on="human",
    # )
    # chain = trimmer | llm
    chain = llm
    chain_with_history = RunnableWithMessageHistory(chain, dummy_get_session_history)
    
    user_state = State(
        question=user_msg,
        )
    print("question: ", user_state["question"])
    user_state["query"] = write_query(user_state)["query"]
    print("query: ", user_state["query"])
    yield(user_state["query"])
    user_state["result"] = execute_query(user_state)["result"]
    print("result: ", user_state["result"])
    prompt = (
        "Given the following user question, corresponding SQL query, and SQL result, answer the user question using them if SQL query and its Result are suitable for answering the question. If they are not suitable, please ignore them.\n\n"
        f'Question: {user_state["question"]}\n'
        f'SQL Query: {user_state["query"]}\n'
        f'SQL Result: {user_state["result"]}'
        
    )
    
    llm_response = ""
    
    for chunk in chain_with_history.stream(
        [HumanMessage(prompt)],
        config={"configurable": {"session_id": "1"}},
    ):
        if chunk.content:
            try:
                yield(chunk.content)
                llm_response += chunk.content
            except:
                yield("")
    bot_msg_obj = ChatHistory(
        id=uuid.uuid4(),
        user_id = client_id,
        role = 'assistant',
        content = llm_response,
        timestamp = datetime.now(timezone.utc)
    )
    db.session.add(bot_msg_obj)
    db.session.commit()
    

    
    