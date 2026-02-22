import os
from langchain_openai import ChatOpenAI

def create_openai_model():
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o"))
