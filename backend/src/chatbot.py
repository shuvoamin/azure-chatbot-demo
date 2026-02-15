import os
from openai import AzureOpenAI
from dotenv import load_dotenv

class ChatBot:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        self._validate_env()

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        
        # Load knowledge base
        self.system_message = self._load_knowledge_base()
        self.history = [{"role": "system", "content": self.system_message}]

    def _load_knowledge_base(self):
        """Load knowledge base from file or use default"""
        knowledge_file = os.path.join(os.path.dirname(__file__), "..", "knowledge_base.md")
        
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r') as f:
                knowledge = f.read()
                return f"You are Nviv, a helpful AI assistant.\n\n{knowledge}\n\nUse this knowledge to answer questions accurately."
        
        # Default if no knowledge base file
        return "You are Nviv, a helpful AI assistant."


    def _validate_env(self):
        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise ValueError("Missing required environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME")

    def chat(self, user_input: str) -> str:
        # Reload knowledge base to pick up any changes
        self.system_message = self._load_knowledge_base()
        self.history[0] = {"role": "system", "content": self.system_message}
        
        self.history.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=self.history
            )
            assistant_response = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            return f"Error: {str(e)}"

    def reset_history(self):
        self.history = [{"role": "system", "content": self.system_message}]
