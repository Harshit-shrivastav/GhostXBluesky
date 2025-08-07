import os
import sys
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebhookData(BaseModel):
    type: str
    post: dict

class GhostToBluesky:
    def __init__(self):
        self.ghost_api_url = os.getenv("GHOST_API_URL")
        self.ghost_admin_key = os.getenv("GHOST_ADMIN_KEY")
        self.bluesky_identifier = os.getenv("BLUESKY_IDENTIFIER")
        self.bluesky_password = os.getenv("BLUESKY_PASSWORD")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        
        required_vars = [
            self.ghost_api_url, 
            self.ghost_admin_key, 
            self.bluesky_identifier, 
            self.bluesky_password,
            self.webhook_secret
        ]
        
        if not all(required_vars):
            logger.error("Missing required environment variables")
            sys.exit(1)
            
        self.session = requests.Session()
        self.bluesky_session = None
        self.session_timeout = 30

    def create_bluesky_session(self) -> bool:
        try:
            response = self.session.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={
                    "identifier": self.bluesky_identifier,
                    "password": self.bluesky_password
                },
                timeout=self.session_timeout
            )
            response.raise_for_status()
            self.bluesky_session = response.json()
            logger.info("Bluesky authentication successful")
            return True
        except Exception as e:
            logger.error(f"Bluesky authentication failed: {e}")
            return False

    def post_to_bluesky(self, text: str) -> bool:
        if not self.bluesky_session:
            if not self.create_bluesky_session():
                return False

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {self.bluesky_session['accessJwt']}"},
                    json={
                        "repo": self.bluesky_session["did"],
                        "collection": "app.bsky.feed.post",
                        "record": {
                            "$type": "app.bsky.feed.post",
                            "text": text,
                            "createdAt": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    timeout=self.session_timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully posted to Bluesky: {text[:50]}...")
                    return True
                elif response.status_code == 401 and attempt < max_retries - 1:
                    logger.warning("Bluesky session expired, re-authenticating...")
                    if not self.create_bluesky_session():
                        return False
                    continue
                else:
                    response.raise_for_status()
            except Exception as e:
                logger.error(f"Error posting to Bluesky (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    return False
        return False

    def format_post_text(self, title: str, url: str, max_length: int = 200) -> str:
        url_length = len(url)
        available_chars = max_length - url_length - 1
        
        if len(title) <= available_chars:
            return f"{title} {url}"
        else:
            truncated_title = title[:available_chars-3].rstrip()
            return f"{truncated_title}... {url}"

    def handle_webhook(self,  dict) -> bool:
        try:
            if data.get('type') != 'post.published':
                logger.info(f"Ignoring event type: {data.get('type')}")
                return True
                
            post = data.get('post', {})
            if not post:
                logger.warning("No post data in webhook")
                return False
                
            title = post.get('title', 'New Post')
            url = post.get('url', '')
            full_url = urljoin(self.ghost_api_url, url)
            
            post_text = self.format_post_text(title, full_url)
            
            logger.info(f"Attempting to post: {post_text}")
            
            if self.post_to_bluesky(post_text):
                logger.info(f"✅ Successfully posted to Bluesky: {title}")
                return True
            else:
                logger.error(f"❌ Failed to post to Bluesky: {title}")
                return False
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False

app = FastAPI()
bridge = GhostToBluesky()

@app.post("/webhook")
async def webhook(webhook_data: WebhookData, authorization: str = Header(None)):
    logger.info("Received webhook request")
    
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Unauthorized webhook request - missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = authorization.split("Bearer ")[1]
    if token != bridge.webhook_secret:
        logger.warning("Unauthorized webhook request - invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if bridge.handle_webhook(webhook_data.dict()):
        logger.info("Webhook processed successfully")
        return {"status": "success"}
    else:
        logger.error("Webhook processing failed")
        raise HTTPException(status_code=500, detail="Processing failed")

@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "GhostxBluesky is running"}

if __name__ == "__main__":
    logger.info("Starting GhostxBluesky...")
    
    if not bridge.create_bluesky_session():
        logger.error("Failed to initialize Bluesky session")
        sys.exit(1)
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    logger.info(f"🚀 Server starting on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
