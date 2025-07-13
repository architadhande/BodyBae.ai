# BodyBae.ai - Your AI Fitness Companion 🌱

A simple, lightweight AI-powered fitness chatbot that helps users with their health and fitness journey.

## Features

- **User Onboarding**: Collects basic health metrics and calculates BMI, BMR, and TDEE
- **Goal Setting**: Helps users set realistic fitness goals with timeframe suggestions
- **FAQ Chatbot**: Answers common fitness, nutrition, and workout questions
- **Daily Tips**: Provides motivational health tips
- **Simple & Clean**: Matcha-themed UI with no complex dependencies

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Render.com compatible
- **No Complex Dependencies**: Works without PyTorch, FAISS, or other heavy libraries

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open browser to `http://localhost:5000`

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Deploy!

## Project Structure

```
bodybae-ai/
├── app.py                  # Flask backend with FAQ logic
├── bodybae_frontend.html   # Frontend UI
├── requirements.txt        # Python dependencies
├── Procfile               # Process file for deployment
└── README.md              # This file
```

## FAQ Knowledge Base

The chatbot uses a simple keyword-based system to answer questions about:
- Protein requirements and sources
- Calorie calculations (BMR, TDEE)
- Workout recommendations (HIIT, strength training)
- Diet and nutrition advice
- Supplement guidance
- Weight loss strategies
- Muscle gain tips

## Future Enhancements

- Database integration for user persistence
- More sophisticated NLP using lightweight models
- Progress tracking features
- Workout and meal plan generators
- Integration with fitness APIs

## License

MIT License - Feel free to use and modify!