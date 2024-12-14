from openai import OpenAI
from src import db
from src.models.user_model import ChatHistory
import os
import httpx
import uuid
from datetime import datetime, timezone

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