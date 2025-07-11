from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os

from config import Config
from services.chatbot import ChatbotService
from services.rag_service import RAGService
from services.progress_tracker import ProgressTracker

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize database
db = SQLAlchemy(app)

# Import models after db initialization
from models.user import User
from models.goal import Goal

# Create tables
with app.app_context():
    db.create_all()

# Initialize services
chatbot_service = ChatbotService()
rag_service = RAGService()
progress_tracker = ProgressTracker(db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        user_id = data.get('user_id', session.get('user_id'))
        
        # Process the message through chatbot
        response = chatbot_service.process_message(message, user_id)
        
        # Store user_id in session if new user
        if 'user_id' in response:
            session['user_id'] = response['user_id']
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['POST'])
def create_user_profile():
    try:
        data = request.json
        user = User(
            name=data['name'],
            age=data['age'],
            height=data['height'],
            weight=data['weight'],
            sex=data['sex'],
            activity_level=data['activity_level']
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        
        return jsonify({
            'status': 'success',
            'user_id': user.id,
            'message': f"Great to meet you, {user.name}! Let's set up your fitness goals."
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/goals', methods=['POST'])
def set_user_goals():
    try:
        data = request.json
        user_id = session.get('user_id') or data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate realistic timeline
        goal_type = data['goal_type']
        target_value = data.get('target_value', 0)
        timeline = calculate_realistic_timeline(user, goal_type, target_value)
        
        goal = Goal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target_value,
            target_date=timeline['target_date'],
            start_date=datetime.utcnow()
        )
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'goal_id': goal.id,
            'realistic_timeline': timeline,
            'message': timeline['message']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/log', methods=['POST'])
def log_progress():
    try:
        data = request.json
        user_id = session.get('user_id') or data.get('user_id')
        
        result = progress_tracker.log_progress(
            user_id=user_id,
            weight=data.get('weight'),
            workout=data.get('workout'),
            calories=data.get('calories')
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tips/daily', methods=['GET'])
def get_daily_tip():
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        tip = chatbot_service.get_daily_tip(user_id)
        return jsonify({'tip': tip})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faq', methods=['POST'])
def answer_faq():
    try:
        question = request.json.get('question', '')
        answer = rag_service.get_answer(question)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_realistic_timeline(user, goal_type, target_value):
    """Calculate realistic timeline based on health standards"""
    current_weight = user.weight
    weeks_needed = 0
    
    if goal_type == 'lose_weight':
        weight_to_lose = current_weight - target_value
        weeks_needed = weight_to_lose / Config.WEIGHT_LOSS_RATE_PER_WEEK
    elif goal_type == 'gain_weight':
        weight_to_gain = target_value - current_weight
        weeks_needed = weight_to_gain / Config.WEIGHT_GAIN_RATE_PER_WEEK
    elif goal_type == 'gain_muscle':
        months_needed = target_value / Config.MUSCLE_GAIN_RATE_PER_MONTH
        weeks_needed = months_needed * 4
    elif goal_type == 'lose_fat':
        weeks_needed = target_value / Config.FAT_LOSS_RATE_PER_WEEK
    else:
        weeks_needed = 12  # Default 3 months for toning/maintenance
    
    target_date = datetime.utcnow() + timedelta(weeks=int(weeks_needed))
    
    return {
        'target_date': target_date.isoformat(),
        'weeks_needed': int(weeks_needed),
        'message': f"Based on healthy standards, you can achieve this goal in approximately {int(weeks_needed)} weeks. Remember, consistency is key!"
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)