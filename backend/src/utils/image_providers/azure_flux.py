import os
import requests
import logging

logger = logging.getLogger(__name__)

class AzureFluxProvider:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.flux_deployment = os.getenv("AZURE_OPENAI_FLUX_DEPLOYMENT")
        
        if not all([self.endpoint, self.api_key, self.flux_deployment]):
            raise ValueError("Missing required environment variables for Azure Flux: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_FLUX_DEPLOYMENT")

    def generate_image(self, prompt: str) -> str:
        flux_url = os.getenv("AZURE_OPENAI_FLUX_URL")
        
        if not flux_url:
            base_url = self.endpoint.replace("cognitiveservices.azure.com", "services.ai.azure.com").rstrip("/")
            flux_url = f"{base_url}/providers/blackforestlabs/v1/{self.flux_deployment}?api-version=preview"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "n": 1,
            "model": "FLUX.2-pro" 
        }

        try:
            logger.info(f"Targeting Image API: {flux_url}")
            response = requests.post(flux_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Image generation failed. Status: {response.status_code}, Body: {response.text}")
                raise RuntimeError(f"Image API returned {response.status_code}: {response.text}")
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                item = data['data'][0]
                if 'b64_json' in item:
                    return f"data:image/png;base64,{item['b64_json']}"
                elif 'url' in item:
                    return item['url']
            
            raise RuntimeError("Image content (url/b64_json) not found in response.")
        except Exception as e:
            if not isinstance(e, RuntimeError):
                logger.error(f"Image generation failed: {str(e)}")
                raise RuntimeError(f"Image generation failed: {str(e)}")
            raise e

def create_azure_flux_provider():
    return AzureFluxProvider()
