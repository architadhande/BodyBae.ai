# 🍵 BodyBae - Your AI Health & Wellness Assistant

BodyBae is an interactive AI chatbot designed to help you with health, fitness, and nutrition questions. It features a beautiful matcha-themed interface, BMI tracking, goal setting, and uses RAG (Retrieval-Augmented Generation) for context-aware responses.

## ✨ Features

- **Intelligent Chat**: Uses text embeddings and RAG for understanding and answering health-related questions
- **BMI Calculator & Tracking**: Automatically calculates and visualizes your BMI
- **Goal Setting**: Set and track your health and fitness goals
- **Personalized Responses**: Considers your profile and goals when providing advice
- **Beautiful Matcha Theme**: Calming green interface inspired by matcha tea
- **Knowledge Base**: Built-in knowledge about nutrition, exercise, health, and lifestyle

## 🚀 Quick Start

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd bodybae
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the setup script (optional, for faster first load):
```bash
chmod +x setup.sh
./setup.sh
```

5. Run the application:
```bash
streamlit run bodybae_main.py
```

### 🌐 Deploy to Render (Free Tier)

1. Fork this repository to your GitHub account

2. Create a new Web Service on [Render](https://render.com):
   - Connect your GitHub repository
   - Choose "Python" as the environment
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `streamlit run bodybae_main.py --server.port=$PORT --server.address=0.0.0.0`

3. Add environment variables (if needed):
   - `PYTHON_VERSION`: 3.9

4. Deploy! The free tier should handle this lightweight application well.

## 📁 Project Structure

```
bodybae/
├── bodybae_main.py      # Main Streamlit application
├── rag.py               # RAG system implementation
├── requirements.txt     # Python dependencies
├── Procfile            # Render deployment configuration
├── setup.sh            # Setup script for model caching
├── .streamlit/
│   └── config.toml     # Streamlit configuration
└── README.md           # This file
```

## 🎯 How It Works

### RAG System
The chatbot uses a Retrieval-Augmented Generation approach:
1. **Text Embeddings**: Converts user queries and knowledge base into vector representations
2. **Similarity Search**: Finds the most relevant information from the knowledge base
3. **Context-Aware Responses**: Generates responses based on relevant knowledge and user profile

### Knowledge Base
The built-in knowledge base covers:
- **Nutrition**: Balanced diet, protein intake, hydration, weight loss
- **Exercise**: Cardio, strength training, flexibility, recovery
- **Health**: BMI interpretation, mental health, sleep, preventive care
- **Lifestyle**: Habit formation, stress management, work-life balance

## 🎨 Customization

### Modifying the Theme
Edit the color scheme in `bodybae_main.py` CSS section:
```css
:root {
    --matcha-dark: #2d4a2b;
    --matcha-medium: #4a7c47;
    --matcha-light: #8bc34a;
    --matcha-cream: #f1f8e9;
    --matcha-accent: #689f38;
}
```

### Expanding the Knowledge Base
Add new topics in `rag.py` under the `_load_knowledge_base()` method:
```python
"category_name": [
    {
        "topic": "your topic",
        "content": "detailed information",
        "keywords": ["relevant", "keywords"]
    }
]
```

## ⚙️ Technical Details

- **Model**: Uses `sentence-transformers/all-MiniLM-L6-v2` for efficient embeddings
- **Framework**: Built with Streamlit for easy deployment
- **Compute**: CPU-only for free tier compatibility
- **Storage**: Uses local JSON for user data (consider database for production)

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Sentence Transformers for the embedding model
- Streamlit for the web framework
- The open-source community for inspiration

---

Made with 🍵 and ❤️ for your health journey!