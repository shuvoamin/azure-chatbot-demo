import os
import requests
import re
import requests
from fastapi import APIRouter, Request, Form, Response, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient
import app_state
from utils.image_utils import save_base64_image

router = APIRouter()

@router.post("/twilio/whatsapp")
async def twilio_whatsapp_webhook(background_tasks: BackgroundTasks, request: Request, Body: str = Form(None), From: str = Form(...), MediaUrl0: str = Form(None), MediaContentType0: str = Form(None)):
    """
    Twilio Messaging Endpoint (WhatsApp/SMS).
    Receives incoming messages from Twilio, acknowledges receipt immediately with an empty TwiML response, 
    and dispatches the message to a background task for processing.
    """
    app_state.logger.info(f"Received Twilio message from {From}")
    host_url = f"{request.url.scheme}://{request.url.netloc}"
    if "azurewebsites.net" in host_url: host_url = host_url.replace("http://", "https://")
    background_tasks.add_task(process_twilio_whatsapp_background, Body, From, MediaUrl0, MediaContentType0, host_url)
    return Response(content=str(MessagingResponse()), media_type="application/xml")

async def process_twilio_whatsapp_background(body: str, from_number: str, media_url: str, media_type: str, host_url: str):
    app_state.logger.info(f"Starting Twilio background task for {from_number}")
    try:
        user_text = body or ""
        if media_url and "audio" in media_type:
            audio_response = requests.get(media_url)
            if audio_response.status_code == 200:
                user_text = app_state.chatbot.transcribe_audio(audio_response.content)
        if user_text or media_url:
            ai_response = await app_state.chatbot.chat(
                f"{user_text}\n\n[Instruction: Keep your response under 1500 characters.]",
                thread_id=from_number
            )
        
        # Check if the AI generated an image (markdown format: ![alt](url))
        image_match = re.search(r'!\[.*?\]\((.*?)\)', ai_response)
        if image_match:
            image_url = image_match.group(1)
            text_without_image = re.sub(r'!\[.*?\]\(.*?\)', '', ai_response).strip()
            send_twilio_reply(from_number, text_without_image, image_url)
        else:
            send_twilio_reply(from_number, ai_response)
    except Exception as e:
        app_state.logger.error(f"Error in Twilio background task: {e}")
        send_twilio_reply(from_number, "Sorry, I encountered an error processing your query.")

def send_twilio_reply(to_number: str, message_text: str, image_url: str = None):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if not all([account_sid, auth_token, from_number]):
        app_state.logger.error("CRITICAL: Twilio credentials missing!")
        return
    try:
        client = TwilioClient(account_sid, auth_token)
        params = {"from_": from_number, "to": to_number}
        if message_text:
            params["body"] = message_text
        if image_url:
            app_state.logger.info(f"Adding media_url to Twilio params: {image_url}")
            params["media_url"] = [image_url]
            

            
        msg_instance = client.messages.create(**params)
        app_state.logger.info(f"Twilio background reply sent. SID: {msg_instance.sid}, Status: {msg_instance.status}")
    except Exception as e:
        app_state.logger.error(f"Failed to send Twilio outbound: {str(e)}")