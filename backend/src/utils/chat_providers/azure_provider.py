import os
from langchain_openai import AzureChatOpenAI

def create_azure_model():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    )
