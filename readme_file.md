# 🏃‍♀️ BodyBae.ai - AI Health & Fitness Chatbot

An intelligent health and fitness chatbot powered by RAG (Retrieval-Augmented Generation) technology, providing personalized health advice, workout plans, and nutrition guidance.

## ✨ Features

- **🤖 AI-Powered Chat**: Advanced RAG system with health-specific knowledge base
- **📊 BMI Calculator**: Real-time BMI calculation and health category assessment
- **👤 Personalized Advice**: Tailored recommendations based on user profile
- **💬 Interactive UI**: Modern, responsive chat interface
- **🎯 Health Goals**: Personalized fitness and nutrition guidance
- **📱 Mobile Friendly**: Works seamlessly on all devices

## 🚀 Live Demo

Visit: [Your Render URL will appear here after deployment]

## 🛠 Tech Stack

- **Backend**: Flask (Python)
- **AI/ML**: LangChain, ChromaDB, Sentence Transformers
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Deployment**: Render
- **Database**: In-memory storage (ChromaDB for vectors)

## 📋 Prerequisites

- Python 3.11+
- Git

## 🔧 Local Development

1. **Clone the repository**
```bash
git clone https://github.com/architadhande/BodyBae.ai.git
cd BodyBae.ai
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

4. **Set environment variables**
```bash
export SECRET_KEY=your-secret-key-here
export FLASK_ENV=development
```

5. **Run the application**
```bash
python bodybae_main.py
```

6. **Open in browser**
```
http://localhost:5000
```

## 🚀 Deployment on Render

### Step 1: Prepare Repository
1. Push all files to GitHub
2. Ensure all files are committed

### Step 2: Create Render Service
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your repository: `architadhande/BodyBae.ai`

### Step 3: Configure Settings
- **Name**: `bodybae-ai`
- **Region**: Choose your preferred region
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bodybae_main.py`

### Step 4: Environment Variables
Add these in Render dashboard:
```
SECRET_KEY=your-super-secret-random-key-32-chars-minimum
FLASK_ENV=production
PORT=5000
```

### Step 5: Deploy
Click "Create Web Service" and wait 5-10 minutes for deployment.

## 📁 Project Structure

```
BodyBae.ai/
├── bodybae_main.py          # Main Flask application
├── rag_system.py           # RAG system for AI responses
├── requirements.txt        # Python dependencies
├── runtime.txt            # Python version specification
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── chroma_health_db/      # Vector database (auto-created)
```

## 🧠 How the RAG System Works

1. **Knowledge Base**: Pre-loaded with comprehensive health & fitness information
2. **Vector Search**: User questions are converted to embeddings and matched with relevant knowledge
3. **Context Generation**: Retrieved information is combined with user profile
4. **Personalized Response**: AI generates contextual, personalized health advice

## 💡 Key Features Explained

### BMI Calculator
- Real-time BMI calculation using Mifflin-St Jeor equation
- Health category classification (Underweight, Normal, Overweight, Obese)
- Personalized advice based on BMI category

### Personalized Chat
- User profile integration (age, gender, activity level, BMI)
- Context-aware responses
- Health goal-specific advice

### Knowledge Domains
- Weight Loss & Management
- Muscle Building & Strength Training
- Cardiovascular Health
- Nutrition & Diet Planning
- Sleep & Recovery
- Exercise Programming
- Lifestyle & Wellness

## 🔒 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `PORT` | Port number (auto-set by Render) | No |

## 🐛 Troubleshooting

### Build Failures
- Check `requirements.txt` for correct package versions
- Ensure Python 3.11 is specified in `runtime.txt`
- Verify all files are committed to GitHub

### RAG System Issues
- If RAG fails to load, app falls back to simple responses
- Check logs for dependency installation errors
- Ensure sufficient memory allocation

### Chat Not Working
- Verify `SECRET_KEY` is set in environment variables
- Check browser console for JavaScript errors
- Ensure proper CORS settings if needed

## 📊 Performance Notes

- **First Load**: May take 30-60 seconds on free tier (cold start)
- **RAG Initialization**: 10-20 seconds for vector database setup
- **Response Time**: 1-3 seconds for AI-generated responses
- **Memory Usage**: ~500MB RAM for full functionality

## 🔮 Future Enhancements

- [ ] User accounts and persistent data
- [ ] Workout plan generation
- [ ] Meal planning features
- [ ] Progress tracking charts
- [ ] Integration with fitness APIs
- [ ] Multi-language support
- [ ] Voice chat capabilities

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Archita Dhande**
- GitHub: [@architadhande](https://github.com/architadhande)

## 🙏 Acknowledgments

- LangChain for RAG framework
- Hugging Face for embeddings models
- Render for hosting platform
- Health & fitness experts for knowledge validation

---

**Built with ❤️ for a healthier world** 🌍