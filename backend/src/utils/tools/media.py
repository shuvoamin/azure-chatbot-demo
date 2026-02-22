import os
import requests
import base64
import uuid
import io
from PIL import Image

from utils.model_registry import ImageFactory

def generate_image(prompt: str) -> str:
    """
    Generates an image using the configured Image Provider based on the user's prompt.
    Returns a markdown image link to display to the user.
    
    Args:
        prompt: A descriptive text prompt for the image generation.
    """
    try:
        # 1. Get the provider from the factory
        provider_name = os.getenv("IMAGE_MODEL_PROVIDER", "azure-flux")
        provider = ImageFactory.get_provider(provider_name)
        
        # 2. Generate the image (returns base64 or URL)
        image_result = provider.generate_image(prompt)
        
        if not image_result:
             return "Error: Image content not found in response."

        # If it's already a public URL returned by some provider, just return it
        if image_result.startswith("http") and not image_result.startswith("data:image"):
            return f"![Generated Image]({image_result})"

        # If it's base64, save it locally to serve it
        image_data = None
        if image_result.startswith("data:image"):
            image_data = image_result.split(",")[1]
        else:
            # Assume raw base64 if no prefix
            image_data = image_result

        # Save Image locally
        filename = f"{uuid.uuid4()}.jpg"
        
        # Determine path relative to THIS file
        # this file is in backend/src/utils/tools/media.py
        # root is ../../../../
        # static is backend/static/generated_images
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
        images_dir = os.path.join(project_root, "backend", "static", "generated_images")
        
        # Fallback if path resolution fails (e.g. running from root)
        if not os.path.exists(os.path.join(project_root, "backend")):
             # Try absolute path based on CWD if running from root
             images_dir = os.path.abspath("backend/static/generated_images")

        os.makedirs(images_dir, exist_ok=True)
        
        filepath = os.path.join(images_dir, filename)
        
        # Decode and save
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(filepath, "JPEG", quality=85)
        
        # Construct public URL
        # Use relative path for web app compatibility (proxied via Vite)
        # If BASE_URL is set (e.g. for prod/ngrok), use it. Otherwise relative.
        base_app_url = os.getenv("BASE_URL")
        if base_app_url:
            public_url = f"{base_app_url.rstrip('/')}/static/generated_images/{filename}"
        else:
             public_url = f"/static/generated_images/{filename}"
        
        return f"![Generated Image]({public_url})"

    except Exception as e:
        return f"Error generating image: {str(e)}"
