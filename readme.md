# BodyBae.ai - AI Fitness Companion

An AI-powered fitness chatbot that provides personalized health and fitness guidance using RAG (Retrieval-Augmented Generation) technology.

## Features

- **User Onboarding**: Collect basic health metrics (height, weight, age, etc.)
- **BMI Calculation**: Automatic BMI calculation with health advice
- **Goal Setting**: Choose from various fitness goals with realistic timelines
- **AI Chat Support**: Ask questions about fitness, nutrition, and workouts
- **Daily Tips**: Get motivational fitness tips
- **Personalized Responses**: Answers tailored to your profile and goals

## Tech Stack

- **Backend**: Flask (Python)
- **AI/LLM**: LangChain + OpenAI API
- **Vector Store**: FAISS (for RAG)
- **Frontend**: Pure HTML/CSS/JavaScript
- **Deployment**: Render.com

## Setup Instructions

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd bodybae-ai
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Run the application**
```bash
python app.py
```

6. **Open the frontend**
- Open `index.html` in your browser
- Update the `API_URL` in the script to `http://localhost:5000/api`

### Deployment to Render

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

2. **Deploy on Render**
- Go to [Render Dashboard](https://dashboard.render.com/)
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Use these settings:
  - **Environment**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn app:app`
- Add environment variable:
  - **Key**: `OPENAI_API_KEY`
  - **Value**: Your OpenAI API key

3. **Update Frontend**
- After deployment, update the `API_URL` in `index.html` to your Render URL:
```javascript
const API_URL = 'https://your-app-name.onrender.com/api';
```

4. **Host Frontend**
- Option 1: GitHub Pages (for the HTML file)
- Option 2: Netlify (drag and drop the HTML file)
- Option 3: Include in the Flask app as a static file

## API Endpoints

- `POST /api/onboard` - User registration and BMI calculation
- `POST /api/set_goal` - Set fitness goals
- `POST /api/chat` - Chat with AI assistant
- `GET /api/daily_tip` - Get daily fitness tip
- `GET /health` - Health check endpoint

## Knowledge Base Topics

The RAG system includes information about:
- BMI calculation and categories
- Calorie requirements (BMR/TDEE)
- Macronutrient ratios
- HIIT workouts
- Home exercises
- Weight loss strategies
- Muscle building
- Supplements
- Progress tracking
- And more!

## Customization

### Adding Knowledge
Edit the `KNOWLEDGE_BASE` array in `app.py` to add more fitness topics:
```python
KNOWLEDGE_BASE.append({
    "topic": "Your Topic",
    "content": "Detailed information about the topic..."
})
```

### Modifying Daily Tips
Update the `DAILY_TIPS` array to add custom motivational messages.

### Styling
The frontend uses a matcha green color scheme. Modify CSS variables in `index.html` to change colors.

## Security Notes

- Never commit your `.env` file with API keys
- Use environment variables for sensitive data
- Consider rate limiting for production use
- Add user authentication for persistent data

## Future Enhancements

- User authentication and data persistence
- Workout plan generation
- Meal plan suggestions
- Progress visualization charts
- Integration with fitness trackers
- Multi-language support

## License

MIT License

## Support

For issues or questions, please open a GitHub issue.