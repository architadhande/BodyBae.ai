# BodyBae.ai Deployment Guide for Render

## Prerequisites
1. A GitHub account
2. A Render account (sign up at render.com)
3. An OpenAI API key (get one at platform.openai.com)

## Step 1: Prepare Your Project

1. Create a new GitHub repository named `bodybae-ai`
2. Clone the repository to your local machine
3. Copy all the project files into the repository
4. Create a `.gitignore` file:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
instance/
.webassets-cache
.scrapy
docs/_build/
target/
.ipynb_checkpoints
.python-version
celerybeat-schedule
*.sage.py
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.spyderproject
.spyproject
.ropeproject
/site
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
chroma_db/
bodybae.db
```

## Step 2: Set Up Environment Variables

1. Copy `.env.example` to `.env`
2. Add your OpenAI API key to the `.env` file
3. Generate a secure secret key for Flask

## Step 3: Test Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Visit http://localhost:5000 to test the application

## Step 4: Push to GitHub

```bash
git add .
git commit -m "Initial commit - BodyBae.ai"
git push origin main
```

## Step 5: Deploy to Render

1. Log in to your Render account
2. Click "New +" → "Web Service"
3. Connect your GitHub account if not already connected
4. Select your `bodybae-ai` repository
5. Configure the service:
   - **Name**: bodybae-ai
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

6. Add environment variables:
   - Click "Environment" tab
   - Add the following:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `SECRET_KEY`: A secure secret key
     - `FLASK_ENV`: production

7. Click "Create Web Service"

## Step 6: Set Up the Database

The free PostgreSQL database will be automatically created based on the `render.yaml` configuration. The connection will be established automatically.

## Step 7: Access Your Application

1. Wait for the build and deployment to complete (5-10 minutes)
2. Your app will be available at: `https://bodybae-ai.onrender.com`
3. The free tier may have cold starts (first request takes 30-60 seconds)

## Troubleshooting

### If the app doesn't start:
1. Check the logs in Render dashboard
2. Ensure all environment variables are set correctly
3. Verify Python version matches (3.11.7)

### If you get import errors:
1. Make sure all files have proper `__init__.py` files
2. Check that the file structure matches exactly

### If the database connection fails:
1. Check that DATABASE_URL is properly set
2. Ensure the database service is running in Render

## Next Steps

1. **Custom Domain**: Add a custom domain in Render settings
2. **Monitoring**: Set up alerts for downtime
3. **Scaling**: Upgrade to paid tier for better performance
4. **Features**: Implement the workout and diet chatbot modules

## Maintenance

- The free tier spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Free tier includes 750 hours/month of running time
- Database backups are not included in free tier

## Security Notes

1. Never commit `.env` file to GitHub
2. Rotate your API keys regularly
3. Use environment variables for all sensitive data
4. Enable 2FA on both GitHub and Render accounts