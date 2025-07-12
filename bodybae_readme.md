# BodyBae.ai - AI Fitness Companion

An AI-powered chatbot that helps users set and achieve health and fitness goals with personalized advice, BMI calculation, and RAG-based Q&A.

## Features

- **User Onboarding**: Collect user metrics (height, weight, age, activity level)
- **BMI Calculation**: Real-time BMI calculation with health advice
- **Goal Setting**: Support for various fitness goals (weight loss, muscle gain, etc.)
- **AI Chat**: RAG-powered responses using PDF knowledge base
- **Daily Tips**: Motivational messages and health tips
- **Progress Tracking**: Log workouts and weight updates

## Tech Stack

- **Backend**: FastAPI
- **RAG System**: LangChain with OpenAI
- **Frontend**: Vanilla HTML/CSS/JS with Matcha green theme
- **Knowledge Base**: PDF support with fallback responses
- **Deployment**: Optimized for Render.com free tier

## Local Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd bodybae-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

4. Add your PDF knowledge base (optional):
   - Place your fitness guide PDF as `home_hiit_guide.pdf` in the root directory
   - The system will automatically extract and use it for RAG

5. Run the application:
```bash
python main.py
```

6. Open browser to `http://localhost:8000`

## Deployment on Render.com

1. Fork/clone this repository to your GitHub account

2. Create a new Web Service on Render:
   - Connect your GitHub account
   - Select this repository
   - Use the following settings:
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py`

3. Add environment variables in Render:
   - `OPENAI_API_KEY`: Your OpenAI API key (optional - works without it using fallback)

4. Deploy! The app will be available at `https://your-app-name.onrender.com`

## File Structure

```
bodybae-ai/
├── main.py              # FastAPI backend server
├── rag.py               # RAG system with PDF support
├── index.html           # Frontend UI
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md           # This file
└── home_hiit_guide.pdf  # Optional PDF knowledge base
```

## API Endpoints

- `GET /` - Serve frontend
- `POST /api/onboard` - User onboarding and BMI calculation
- `POST /api/set_goal` - Set fitness goals
- `POST /api/chat` - Chat with AI assistant
- `POST /api/progress` - Log progress updates
- `GET /api/daily_tip` - Get daily motivational tip
- `GET /health` - Health check endpoint

## Usage Example

1. **Onboarding**: Fill out the form with your details
2. **BMI Display**: See your BMI and health category
3. **Goal Setting**: Choose from 7 fitness goals
4. **Chat**: Ask questions about fitness, nutrition, workouts
5. **Track Progress**: Log your weight and workouts

## Notes for Render Free Tier

- The app uses minimal resources suitable for free tier
- PDF processing is done in-memory
- No persistent storage (data resets on restart)
- Fallback responses work without OpenAI API key
- Auto-sleeps after 15 minutes of inactivity

## License

MIT License