# GhostXBluesky 

Automatically post your Ghost blog articles to Bluesky the moment you hit "Publish"! No more manual cross-posting - this webhook-based bridge does all the work for you.

## 🚀 Features

- **Instant Posting**: Posts to Bluesky immediately when you publish in Ghost
- **Smart Formatting**: Automatically truncates titles to 200 characters with "..." + link
- **Zero Configuration**: Just set up the webhook and you're good to go
- **Reliable**: Automatic retry logic and session management
- **Lightweight**: Minimal resource usage with FastAPI

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file:
```bash
GHOST_API_URL=https://yourblog.com
GHOST_ADMIN_KEY=your_ghost_admin_api_key
BLUESKY_IDENTIFIER=your_handle.bsky.social
BLUESKY_PASSWORD=your_app_password
WEBHOOK_SECRET=generate_a_secure_secret_here
```

### 3. Get Your Ghost Admin API Key
1. Go to Ghost Admin → Settings → Integrations
2. Create a new custom integration
3. Enable "Admin API" key
4. Copy the key

### 4. Create Bluesky App Password
1. In Bluesky app: Settings → App Passwords
2. Generate a new password with "Post" permissions

### 5. Generate Webhook Secret
You can create a secure webhook secret using any of these methods:

**Option 1: Command Line (Recommended)**
```bash
# Using OpenSSL (most common)
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option 2: Online Generators**
- Visit [https://www.avast.com/en-in/random-password-generator](https://www.avast.com/en-in/random-password-generator)
- Click "Copy" Button
- Generate a 50-character key

### 6. Configure Ghost Webhook
1. In Ghost Admin → Settings → Labs → Webhooks
2. Add new webhook:
   - **Name**: Bluesky Bridge
   - **Event**: Post published
   - **Target URL**: `http://your-server.com:8000/webhook`
   - **Secret**: Your generated `WEBHOOK_SECRET` value

### 7. Run the Service
```bash
python main.py 8080
```

## 🐳 Docker Support (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["python", "main.py", "8080"]
```

## 🔧 Production Deployment

### Using tmux (Recommended for simplicity)
```bash
# Install tmux
sudo apt install tmux

# Start persistent session
tmux new-session -d -s ghost-bluesky
tmux send-keys -t ghost-bluesky 'cd /path/to/script' Enter
tmux send-keys -t ghost-bluesky 'export GHOST_API_URL=https://yourblog.com' Enter
tmux send-keys -t ghost-bluesky 'export GHOST_ADMIN_KEY=your_key' Enter
tmux send-keys -t ghost-bluesky 'export BLUESKY_IDENTIFIER=your_handle.bsky.social' Enter
tmux send-keys -t ghost-bluesky 'export BLUESKY_PASSWORD=your_app_password' Enter
tmux send-keys -t ghost-bluesky 'export WEBHOOK_SECRET=your_secret' Enter
tmux send-keys -t ghost-bluesky 'python main.py 8000' Enter

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t ghost-bluesky
```

## 📝 How It Works

1. You publish a post in Ghost
2. Ghost sends a webhook to this service
3. The service formats your post title + link
4. Posts immediately to your Bluesky timeline

Example output:
```
Just published a new article about Python web development! 
https://yourblog.com/python-web-dev
```

## Follow Me For More

[![Bluesky](https://img.shields.io/badge/Bluesky-0285FF?style=for-the-badge&logo=bluesky&logoColor=white)](https://bsky.app/profile/h-s.site)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Harshit-shrivastav)

## 📄 License

MIT License - Feel free to use, modify, and distribute as you see fit!

## 💡 Tips

- Generate a strong webhook secret: `openssl rand -hex 32`
- Use a reverse proxy (nginx) for HTTPS in production
- Check service health: `curl http://localhost:8080/health`
