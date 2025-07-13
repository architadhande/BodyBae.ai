# BodyBae.ai Deployment Guide for Render

## Step-by-Step Deployment Instructions

### 1. Prepare Your Code

Create a new folder for your project and add these files:
- `app.py` (the backend code)
- `bodybae_frontend.html` (your frontend - save it in the same directory as app.py)
- `requirements.txt`
- `Procfile`

### 2. Initialize Git Repository

```bash
git init
git add .
git commit -m "Initial commit - BodyBae.ai"
```

### 3. Create GitHub Repository

1. Go to GitHub and create a new repository
2. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/bodybae-ai.git
   git branch -M main
   git push -u origin main
   ```

### 4. Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub account if not already connected
4. Select your `bodybae-ai` repository
5. Configure the service:
   - **Name**: bodybae-ai (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
6. Click "Create Web Service"

### 5. Wait for Deployment

Render will:
- Clone your repository
- Install dependencies
- Start your application
- Provide you with a URL like `https://bodybae-ai.onrender.com`

### 6. Test Your Application

Visit your Render URL and test:
1. Fill out the onboarding form
2. Set a fitness goal
3. Chat with the bot about fitness topics

## Troubleshooting

### If the frontend doesn't load:
- Make sure `bodybae_frontend.html` is in the same directory as `app.py`
- Check that the static file serving is working in Flask

### If the chat doesn't respond:
- Check Render logs for any errors
- Ensure all API endpoints are returning proper JSON

### If deployment fails:
- Check that all required files are committed to Git
- Verify Python version compatibility
- Check Render logs for specific error messages

## Local Testing Before Deployment

Always test locally first:
```bash
python app.py
```
Then visit `http://localhost:5000` to ensure everything works.

## Cost

This setup uses:
- Render Free Tier: $0/month
- No external APIs or databases
- Simple in-memory storage (resets on restart)

## Next Steps

After successful deployment, consider:
1. Adding a database for persistent storage
2. Implementing user authentication
3. Enhancing the FAQ system with more responses
4. Adding progress tracking features