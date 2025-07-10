from flask import Flask, request, jsonify, session
import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional

# Import systems
try:
    from rag_system import HealthRAGSystem
    RAG_AVAILABLE = True
    print("✅ RAG system imported")
except ImportError as e:
    print(f"⚠️ RAG system not available: {e}")
    RAG_AVAILABLE = False

try:
    import openai
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    OPENAI_AVAILABLE = bool(openai.api_key)
    print(f"✅ OpenAI: {'Available' if OPENAI_AVAILABLE else 'No API key'}")
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Storage
users_db = {}
chat_history_db = {}

# Initialize systems
rag_system = None
if RAG_AVAILABLE:
    try:
        rag_system = HealthRAGSystem()
        print("✅ RAG system initialized")
    except Exception as e:
        print(f"⚠️ RAG init failed: {e}")

class AdvancedHealthAI:
    def __init__(self):
        self.health_goals = [
            "Weight Loss", "Muscle Building", "Strength Training", "Cardiovascular Health",
            "Flexibility & Mobility", "Athletic Performance", "General Wellness", 
            "Weight Gain", "Body Recomposition", "Injury Recovery", "Mental Health",
            "Sleep Optimization", "Nutrition Education", "Habit Building"
        ]
    
    def calculate_health_metrics(self, user_data):
        """Calculate comprehensive health metrics"""
        weight = user_data['weight']
        height = user_data['height'] / 100  # Convert to meters
        age = user_data['age']
        gender = user_data['gender']
        activity = user_data['activity']
        
        # BMI
        bmi = weight / (height ** 2)
        
        # BMR (Mifflin-St Jeor)
        if gender.lower() == 'male':
            bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * (height * 100) - 5 * age - 161
        
        # TDEE
        multipliers = {"sedentary": 1.2, "lightly_active": 1.375, "moderately_active": 1.55, "very_active": 1.725, "extremely_active": 1.9}
        tdee = bmr * multipliers.get(activity, 1.2)
        
        # BMI Category
        if bmi < 18.5: category = "Underweight"
        elif bmi < 25: category = "Normal Weight"
        elif bmi < 30: category = "Overweight"
        else: category = "Obese"
        
        return {
            'bmi': round(bmi, 1),
            'bmi_category': category,
            'bmr': round(bmr),
            'tdee': round(tdee),
            'protein_needs': round(weight * 1.6, 1),  # grams
            'water_needs': round(weight * 35),  # ml
        }

    async def get_intelligent_response(self, message, user_profile, conversation_history):
        """Get response using OpenAI + RAG"""
        
        # Build comprehensive context
        context = self._build_context(user_profile, conversation_history)
        
        # Get RAG knowledge
        rag_context = ""
        if rag_system:
            try:
                rag_response = rag_system.get_health_response(message, user_profile)
                rag_context = f"RAG Knowledge: {rag_response}\n\n"
            except Exception as e:
                print(f"RAG error: {e}")
        
        # Use OpenAI if available
        if OPENAI_AVAILABLE:
            try:
                response = await self._get_openai_response(message, context, rag_context)
                return response
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        # Fallback to RAG only
        if rag_system:
            try:
                return rag_system.get_health_response(message, user_profile)
            except Exception as e:
                print(f"RAG fallback error: {e}")
        
        # Final fallback
        return self._get_basic_response(message, user_profile)
    
    async def _get_openai_response(self, message, context, rag_context):
        """Get response from OpenAI GPT"""
        
        system_prompt = f"""You are BodyBae, an advanced AI health and fitness coach with expertise in:
- Exercise physiology and biomechanics
- Nutrition science and metabolism  
- Behavioral psychology and habit formation
- Sports medicine and injury prevention
- Mental health and wellness

You provide evidence-based, personalized advice that's practical and actionable.

{context}

{rag_context}

Guidelines:
- Be encouraging and motivational
- Provide specific, actionable advice
- Include scientific rationale when relevant
- Ask follow-up questions to better help
- Acknowledge limitations and suggest professional help when appropriate
- Keep responses conversational but informative
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
    
    def _build_context(self, user_profile, conversation_history):
        """Build comprehensive user context"""
        if not user_profile:
            return "No user profile available."
        
        context = f"""
User Profile:
- Name: {user_profile.get('name', 'User')}
- Age: {user_profile.get('age')} years old
- Gender: {user_profile.get('gender')}
- Height: {user_profile.get('height')}cm, Weight: {user_profile.get('weight')}kg
- BMI: {user_profile.get('bmi')} ({user_profile.get('bmi_category')})
- Activity Level: {user_profile.get('activity')}
- Daily Calories: {user_profile.get('tdee')}
- Protein Needs: {user_profile.get('protein_needs')}g
- Goals: {', '.join(user_profile.get('goals', []))}

Recent Conversation:
{self._format_conversation_history(conversation_history)}
"""
        return context
    
    def _format_conversation_history(self, history):
        """Format conversation history"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history[-6:]:  # Last 3 exchanges
            role = "User" if msg['role'] == 'user' else "BodyBae"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _get_basic_response(self, message, user_profile):
        """Basic fallback response"""
        name = user_profile.get('name', 'there') if user_profile else 'there'
        return f"Hi {name}! I'm here to help with your health and fitness journey. I can provide guidance on nutrition, exercise, and wellness. Could you tell me more about what specific area you'd like help with?"

# Initialize AI
health_ai = AdvancedHealthAI()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>BodyBae.ai - Intelligent Health Coach</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: #424106;
            min-height: 100vh;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .welcome { 
            text-align: center; 
            color: white; 
            padding: 60px 20px;
        }
        
        .welcome h1 { 
            font-size: 3rem; 
            margin-bottom: 20px; 
            color: #424106;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .welcome p { 
            font-size: 1.2rem; 
            margin-bottom: 30px; 
            opacity: 0.9;
        }
        
        .start-btn {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
        }
        
        .start-btn:hover { transform: translateY(-2px); }
        
        .chat-container {
            display: none;
            background: white;
            border-radius: 15px;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .chat-layout {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: 80vh;
        }
        
        .sidebar {
            background: #f8f9fa;
            padding: 20px;
            border-right: 1px solid #ddd;
            overflow-y: auto;
        }
        
        .sidebar h3 {
            color: #424106;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            font-size: 0.9rem;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.9rem;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .goals-section {
            margin: 20px 0;
        }
        
        .goals-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
        }
        
        .goal-chip {
            background: #e9ecef;
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .goal-chip:hover,
        .goal-chip.selected {
            background: #A4B07E;
            color: white;
            border-color: #707C4F;
        }
        
        .analyze-btn {
            width: 100%;
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 15px;
        }
        
        .analyze-btn:hover { opacity: 0.9; }
        
        .metrics-display {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            text-align: center;
            display: none;
        }
        
        .metrics-display h4 {
            margin: 0 0 10px 0;
            font-size: 1rem;
        }
        
        .metric-item {
            margin: 5px 0;
            font-size: 0.9rem;
        }
        
        .chat-main {
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h2 {
            margin: 0;
            font-size: 1.5rem;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: linear-gradient(to bottom, white, #f8f9fa);
        }
        
        .message {
            margin: 15px 0;
            padding: 12px 15px;
            border-radius: 15px;
            max-width: 80%;
            line-height: 1.5;
        }
        
        .message.user {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .message.bot {
            background: #f1f3f4;
            color: #424106;
            margin-right: auto;
            border-bottom-left-radius: 5px;
            border: 1px solid #e0e0e0;
        }
        
        .message.system {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            text-align: center;
            margin: 10px auto;
            font-weight: 500;
            max-width: 90%;
        }
        
        .typing {
            background: #f1f3f4;
            color: #666;
            margin-right: auto;
            border-bottom-left-radius: 5px;
            font-style: italic;
            display: none;
        }
        
        .chat-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
        }
        
        .quick-suggestions {
            display: flex;
            gap: 8px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .quick-btn {
            background: #e9ecef;
            border: 1px solid #ddd;
            padding: 6px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .quick-btn:hover {
            background: #A4B07E;
            color: white;
        }
        
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            border: 2px solid #ddd;
            border-radius: 20px;
            padding: 10px 15px;
            font-size: 1rem;
            resize: none;
            max-height: 100px;
            font-family: inherit;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: #A4B07E;
        }
        
        .send-btn {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-btn:hover { opacity: 0.9; }
        
        @media (max-width: 768px) {
            .chat-layout {
                grid-template-columns: 1fr;
                height: auto;
            }
            .sidebar {
                max-height: 40vh;
                order: 2;
            }
            .chat-main {
                order: 1;
                height: 50vh;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Welcome Screen -->
        <div id="welcome" class="welcome">
            <h1>BodyBae.ai</h1>
            <p>Intelligent AI Health Coach</p>
            <p>Powered by OpenAI GPT + Advanced RAG System</p>
            <button class="start-btn" onclick="startChat()">Start Health Coaching</button>
            <div id="debug" style="margin-top: 20px; font-size: 0.9rem;"></div>
        </div>

        <!-- Chat Interface -->
        <div id="chat" class="chat-container">
            <div class="chat-layout">
                <!-- Sidebar -->
                <div class="sidebar">
                    <h3>👤 Your Profile</h3>
                    
                    <div class="form-group">
                        <label>Name:</label>
                        <input type="text" id="name" placeholder="Your name">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Age:</label>
                            <input type="number" id="age" min="13" max="100" placeholder="25">
                        </div>
                        <div class="form-group">
                            <label>Gender:</label>
                            <select id="gender">
                                <option value="">Select</option>
                                <option value="male">Male</option>
                                <option value="female">Female</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Height (cm):</label>
                            <input type="number" id="height" min="100" max="250" placeholder="170">
                        </div>
                        <div class="form-group">
                            <label>Weight (kg):</label>
                            <input type="number" id="weight" min="30" max="300" step="0.1" placeholder="70">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Activity Level:</label>
                        <select id="activity">
                            <option value="">Select</option>
                            <option value="sedentary">Sedentary</option>
                            <option value="lightly_active">Lightly Active</option>
                            <option value="moderately_active">Moderately Active</option>
                            <option value="very_active">Very Active</option>
                            <option value="extremely_active">Extremely Active</option>
                        </select>
                    </div>
                    
                    <div class="goals-section">
                        <h3>🎯 Health Goals</h3>
                        <div class="goals-grid" id="goals-grid">
                            <!-- Goals populated by JavaScript -->
                        </div>
                    </div>
                    
                    <button class="analyze-btn" onclick="analyzeProfile()">Analyze Profile</button>
                    
                    <div id="metrics" class="metrics-display">
                        <!-- Health metrics will appear here -->
                    </div>
                </div>

                <!-- Main Chat -->
                <div class="chat-main">
                    <div class="chat-header">
                        <h2>🤖 BodyBae AI Coach</h2>
                        <p>Advanced AI Health & Fitness Expert</p>
                    </div>
                    
                    <div id="messages" class="chat-messages">
                        <div class="message bot">
                            👋 Hi! I'm BodyBae, your advanced AI health coach powered by OpenAI GPT and specialized health knowledge.
                            <br><br>
                            I can help you with:
                            <br>• Personalized workout programs
                            <br>• Nutrition strategies and meal planning  
                            <br>• Science-based health advice
                            <br>• Habit formation and motivation
                            <br>• Injury prevention and recovery
                            <br><br>
                            Fill out your profile on the left, then let's start your health journey! 💪
                        </div>
                        
                        <div id="typing" class="message typing">
                            🤖 BodyBae is thinking...
                        </div>
                    </div>
                    
                    <div class="chat-input-area">
                        <div class="quick-suggestions">
                            <button class="quick-btn" onclick="quickMessage('Create a personalized workout plan')">Workout Plan</button>
                            <button class="quick-btn" onclick="quickMessage('Design my nutrition strategy')">Nutrition Plan</button>
                            <button class="quick-btn" onclick="quickMessage('Help with weight loss')">Weight Loss</button>
                            <button class="quick-btn" onclick="quickMessage('Build muscle effectively')">Build Muscle</button>
                            <button class="quick-btn" onclick="quickMessage('Improve my sleep quality')">Better Sleep</button>
                            <button class="quick-btn" onclick="quickMessage('I need motivation')">Motivation</button>
                        </div>
                        
                        <div class="input-wrapper">
                            <textarea id="message-input" class="chat-input" placeholder="Ask me anything about health, fitness, nutrition..." rows="1"></textarea>
                            <button class="send-btn" onclick="sendMessage()">➤</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let userProfile = null;
        let selectedGoals = [];
        
        const healthGoals = [
            'Weight Loss', 'Muscle Building', 'Strength Training', 'Cardiovascular Health',
            'Flexibility & Mobility', 'Athletic Performance', 'General Wellness', 
            'Weight Gain', 'Body Recomposition', 'Injury Recovery', 'Mental Health',
            'Sleep Optimization', 'Nutrition Education', 'Habit Building'
        ];

        function startChat() {
            console.log('Starting chat...');
            document.getElementById('welcome').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
            initializeGoals();
            document.getElementById('debug').innerHTML = 'Chat loaded! ✅';
        }

        function initializeGoals() {
            const goalsGrid = document.getElementById('goals-grid');
            goalsGrid.innerHTML = '';
            
            healthGoals.forEach(goal => {
                const chip = document.createElement('div');
                chip.className = 'goal-chip';
                chip.textContent = goal;
                chip.onclick = () => toggleGoal(chip, goal);
                goalsGrid.appendChild(chip);
            });
        }

        function toggleGoal(element, goal) {
            if (selectedGoals.includes(goal)) {
                selectedGoals = selectedGoals.filter(g => g !== goal);
                element.classList.remove('selected');
            } else {
                selectedGoals.push(goal);
                element.classList.add('selected');
            }
        }

        async function analyzeProfile() {
            const name = document.getElementById('name').value;
            const age = document.getElementById('age').value;
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            const gender = document.getElementById('gender').value;
            const activity = document.getElementById('activity').value;

            if (!name || !age || !height || !weight || !gender || !activity) {
                addMessage('system', '⚠️ Please fill in all profile fields');
                return;
            }

            if (selectedGoals.length === 0) {
                addMessage('system', '🎯 Please select at least one health goal');
                return;
            }

            addMessage('system', '🔄 Analyzing your health profile...');

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name, age: parseInt(age), height: parseFloat(height), 
                        weight: parseFloat(weight), gender, activity, goals: selectedGoals
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    userProfile = result.profile;
                    displayMetrics(result.metrics);
                    addMessage('bot', result.analysis);
                    
                    setTimeout(() => {
                        addMessage('system', '🚀 Profile complete! Ask me anything about your health goals.');
                    }, 2000);
                } else {
                    addMessage('system', '❌ Error analyzing profile: ' + result.error);
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('system', '🔌 Network error. Please try again.');
            }
        }

        function displayMetrics(metrics) {
            const metricsDiv = document.getElementById('metrics');
            metricsDiv.style.display = 'block';
            metricsDiv.innerHTML = `
                <h4>📊 Your Health Metrics</h4>
                <div class="metric-item">BMI: ${metrics.bmi} (${metrics.bmi_category})</div>
                <div class="metric-item">Daily Calories: ${metrics.tdee}</div>
                <div class="metric-item">Protein: ${metrics.protein_needs}g/day</div>
                <div class="metric-item">Water: ${metrics.water_needs}ml/day</div>
            `;
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;

            addMessage('user', message);
            input.value = '';
            input.style.height = 'auto';
            
            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message, 
                        user_profile: userProfile,
                        selected_goals: selectedGoals
                    })
                });

                const result = await response.json();
                hideTyping();
                addMessage('bot', result.response);
                
            } catch (error) {
                console.error('Error:', error);
                hideTyping();
                addMessage('bot', 'I apologize, but I\'m having trouble right now. Please try again.');
            }
        }

        function quickMessage(message) {
            document.getElementById('message-input').value = message;
            sendMessage();
        }

        function addMessage(sender, message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.innerHTML = message.replace(/\\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTyping() {
            document.getElementById('typing').style.display = 'block';
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }

        function hideTyping() {
            document.getElementById('typing').style.display = 'none';
        }

        // Auto-resize textarea
        document.getElementById('message-input').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        // Enter key support
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        console.log('BodyBae.ai initialized with OpenAI + RAG');
    </script>
</body>
</html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze_profile():
    """Analyze user health profile"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        # Store user data
        user_data = {
            'name': data['name'],
            'age': data['age'],
            'height': data['height'],
            'weight': data['weight'],
            'gender': data['gender'],
            'activity': data['activity'],
            'goals': data['goals'],
            'created_at': datetime.now().isoformat()
        }
        
        users_db[user_id] = user_data
        session['user_id'] = user_id
        
        # Calculate metrics
        metrics = health_ai.calculate_health_metrics(user_data)
        users_db[user_id]['metrics'] = metrics
        
        # Generate analysis
        analysis_message = f"""✅ **Profile Analysis Complete for {data['name']}!**

**Health Metrics:**
• BMI: {metrics['bmi']} ({metrics['bmi_category']})
• Daily Calorie Needs: {metrics['tdee']} calories
• Protein Target: {metrics['protein_needs']}g daily
• Hydration Goal: {metrics['water_needs']}ml daily

**Your Goals:** {', '.join(data['goals'])}

I'm now ready to provide personalized, evidence-based advice tailored to your profile and goals. My responses combine the latest scientific research with practical, actionable recommendations.

What would you like to focus on first? 🎯"""
        
        return jsonify({
            'success': True,
            'profile': {**user_data, **metrics},
            'metrics': metrics,
            'analysis': analysis_message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def intelligent_chat():
    """Main chat endpoint with OpenAI + RAG"""
    data = request.json
    message = data.get('message', '')
    user_profile = data.get('user_profile', {})
    selected_goals = data.get('selected_goals', [])
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message required'})
    
    try:
        # Get conversation history
        conversation_history = get_conversation_history(user_id)
        
        # Get intelligent response
        if OPENAI_AVAILABLE:
            response = get_openai_response(message, user_profile, conversation_history)
        elif rag_system:
            response = rag_system.get_health_response(message, user_profile)
        else:
            response = get_smart_fallback(message, user_profile)
        
        # Store conversation
        store_conversation(user_id, message, response)
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'response': 'I apologize, but I\'m having trouble right now. Could you please rephrase your question?'})

def get_openai_response(message, user_profile, conversation_history):
    """Get response from OpenAI GPT"""
    
    # Build context
    context = build_user_context(user_profile, conversation_history)
    
    # Get RAG knowledge if available
    rag_context = ""
    if rag_system:
        try:
            rag_knowledge = rag_system.get_health_response(message, user_profile)
            rag_context = f"\n\nSpecialized Health Knowledge: {rag_knowledge}"
        except:
            pass
    
    system_prompt = f"""You are BodyBae, an expert AI health and fitness coach with advanced knowledge in:

🧬 EXPERTISE AREAS:
- Exercise Physiology & Biomechanics
- Sports Nutrition & Metabolism
- Behavioral Psychology & Habit Formation  
- Injury Prevention & Recovery
- Mental Health & Wellness
- Sleep Science & Recovery

🎯 PERSONALITY:
- Encouraging and motivational
- Evidence-based and scientific
- Practical and actionable
- Empathetic and supportive
- Enthusiastic about health

📊 USER CONTEXT:
{context}

🧠 SPECIALIZED KNOWLEDGE:
{rag_context}

📋 GUIDELINES:
- Provide specific, actionable advice
- Include scientific rationale when helpful
- Ask follow-up questions to better assist
- Be encouraging and motivational
- Suggest professional help for medical concerns
- Keep responses conversational but informative
- Use emojis sparingly but effectively
- Aim for 150-300 words unless more detail is needed

Respond as BodyBae with expertise, enthusiasm, and practical guidance!"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=600,
            temperature=0.7,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"OpenAI error: {e}")
        # Fallback to RAG if OpenAI fails
        if rag_system:
            return rag_system.get_health_response(message, user_profile)
        else:
            return get_smart_fallback(message, user_profile)

def build_user_context(user_profile, conversation_history):
    """Build comprehensive user context"""
    if not user_profile:
        return "No user profile available. General health guidance will be provided."
    
    context = f"""
👤 USER PROFILE:
- Name: {user_profile.get('name', 'User')}
- Age: {user_profile.get('age')} years, {user_profile.get('gender', 'Unknown')}
- Physical: {user_profile.get('height')}cm, {user_profile.get('weight')}kg
- BMI: {user_profile.get('bmi')} ({user_profile.get('bmi_category', 'Unknown')})
- Activity Level: {user_profile.get('activity', 'Unknown')}
- Health Goals: {', '.join(user_profile.get('goals', ['General wellness']))}

📊 CALCULATED METRICS:
- Daily Calories (TDEE): {user_profile.get('tdee')}
- Protein Needs: {user_profile.get('protein_needs')}g/day
- Hydration Target: {user_profile.get('water_needs')}ml/day

💬 RECENT CONVERSATION:
{format_conversation_history(conversation_history)}
"""
    return context

def format_conversation_history(history):
    """Format recent conversation"""
    if not history:
        return "This is the start of our conversation."
    
    formatted = []
    for msg in history[-4:]:  # Last 2 exchanges
        role = "User" if msg['role'] == 'user' else "BodyBae"
        formatted.append(f"{role}: {msg['content'][:100]}...")
    
    return "\n".join(formatted)

def get_smart_fallback(message, user_profile):
    """Smart fallback when OpenAI/RAG unavailable"""
    message_lower = message.lower()
    name = user_profile.get('name', 'there') if user_profile else 'there'
    
    # Advanced pattern matching
    if any(word in message_lower for word in ['workout', 'exercise', 'training', 'routine', 'program']):
        goals = user_profile.get('goals', []) if user_profile else []
        
        if 'Muscle Building' in goals:
            return f"""Hi {name}! For muscle building, here's a science-based approach:

**🏋️ Training Protocol:**
• 3-4 strength sessions per week
• Progressive overload (increase weight/reps weekly)
• Compound movements: squats, deadlifts, bench press, rows
• 3-4 sets of 6-12 reps for hypertrophy

**💪 Key Principles:**
• Train each muscle group 2x per week
• Rest 48-72 hours between training same muscles
• Focus on form over weight
• Track your lifts to ensure progression

**🥩 Nutrition Support:**
• Protein: {user_profile.get('protein_needs', '1.6-2.2g per kg')}g daily
• Slight caloric surplus: {user_profile.get('tdee', 'TDEE') + 200} calories
• Post-workout: 20-30g protein within 2 hours

Would you like me to design a specific program for your experience level?"""

        elif 'Weight Loss' in goals:
            return f"""Hi {name}! For effective weight loss, let's create a sustainable approach:

**🔥 Exercise Strategy:**
• 3-4 cardio sessions (mix HIIT and steady-state)
• 2-3 strength training sessions (preserve muscle)
• Daily steps: 8,000-10,000

**🍎 Nutrition Approach:**
• Caloric deficit: {user_profile.get('tdee', 2000) - 500} calories daily
• High protein: {user_profile.get('protein_needs', '1.2-1.6g per kg')}g to preserve muscle
• Focus on whole foods, high fiber

**📊 Tracking:**
• Weekly weigh-ins (same time/conditions)
• Body measurements
• Progress photos
• Energy levels

The key is consistency over perfection. What's your biggest challenge with weight loss?"""

        else:
            return f"""Hi {name}! For general fitness, here's a balanced approach:

**🎯 Weekly Structure:**
• 3-4 strength training sessions
• 2-3 cardio sessions (150+ minutes moderate intensity)
• 1-2 flexibility/mobility days

**💪 Strength Focus:**
• Compound movements for efficiency
• Progressive overload principle
• Full-body or upper/lower split

**❤️ Cardio Options:**
• Walking, jogging, cycling, swimming
• Mix steady-state and intervals
• Find activities you enjoy!

**⚖️ Nutrition Balance:**
• Maintain around {user_profile.get('tdee', 'your TDEE')} calories
• Balanced macronutrients
• Plenty of vegetables and water

What specific aspect would you like to dive deeper into?"""

    elif any(word in message_lower for word in ['nutrition', 'diet', 'food', 'eat', 'meal', 'calories']):
        if user_profile:
            tdee = user_profile.get('tdee', 2000)
            protein = user_profile.get('protein_needs', 100)
            goals = user_profile.get('goals', [])
            
            if 'Weight Loss' in goals:
                target_calories = tdee - 500
                return f"""Hi {name}! Here's your personalized nutrition strategy for weight loss:

**📊 Daily Targets:**
• Calories: {target_calories} (500 deficit for 0.5kg/week loss)
• Protein: {protein}g (muscle preservation)
• Water: {user_profile.get('water_needs', 2500)}ml

**🥗 Meal Structure:**
• Protein with every meal (25-30g)
• Half plate vegetables at lunch/dinner
• Complex carbs around workouts
• Healthy fats for satiety

**⏰ Timing Tips:**
• Eat every 3-4 hours
• Larger meals earlier in day
• Post-workout nutrition within 2 hours
• Stop eating 2-3 hours before bed

**🍎 Food Choices:**
• Lean proteins: chicken, fish, eggs, legumes
• Complex carbs: oats, quinoa, sweet potato
• Healthy fats: nuts, olive oil, avocado
• Fiber-rich vegetables and fruits

Would you like specific meal ideas or help with meal prep strategies?"""

            elif 'Muscle Building' in goals:
                target_calories = tdee + 300
                return f"""Hi {name}! Here's your muscle-building nutrition plan:

**📊 Daily Targets:**
• Calories: {target_calories} (moderate surplus)
• Protein: {protein}g (spread throughout day)
• Carbs: Focus around workouts

**💪 Protein Strategy:**
• 20-30g every 3-4 hours
• Complete proteins with all amino acids
• Post-workout: whey/casein protein
• Leucine-rich foods for muscle synthesis

**⚡ Carb Timing:**
• Pre-workout: 30-60g (1-2 hours before)
• Post-workout: 0.5-1g per kg body weight
• Complex carbs for sustained energy

**🥑 Healthy Fats:**
• 20-30% of total calories
• Essential for hormone production
• Include omega-3 fatty acids

**💡 Pro Tips:**
• Don't skip meals
• Quality sleep enhances gains
• Stay hydrated
• Consider creatine supplementation

What specific nutrition questions do you have?"""
            
            else:
                return f"""Hi {name}! Here's balanced nutrition guidance:

**📊 Daily Framework:**
• Calories: Around {tdee} (maintenance)
• Protein: {protein}g daily
• Balanced macronutrients

**🌟 Core Principles:**
• Eat the rainbow (variety of colors)
• Whole foods over processed
• Listen to hunger/fullness cues
• Stay consistently hydrated

**🍽️ Meal Ideas:**
• Breakfast: Oats + berries + protein powder
• Lunch: Quinoa bowl + vegetables + lean protein
• Dinner: Salmon + sweet potato + broccoli
• Snacks: Greek yogurt, nuts, fruits

**💧 Hydration:**
• Target: {user_profile.get('water_needs', 2500)}ml daily
• More on active days
• Monitor urine color

What specific nutrition topic interests you most?"""
        
        else:
            return "I'd love to help with nutrition! To give you personalized advice, could you first fill out your profile on the left? This allows me to calculate your specific calorie and nutrient needs."

    elif any(word in message_lower for word in ['motivation', 'give up', 'struggling', 'hard', 'difficult', 'discouraged']):
        return f"""Hey {name}, I hear you! 🌟 Struggling is completely normal and actually shows you're pushing your comfort zone.

**🧠 Remember Your Why:**
{f"Your goals: {', '.join(user_profile.get('goals', []))}" if user_profile else "Think about why you started this journey"}

**💪 Reframe Your Mindset:**
• Progress isn't always linear
• Setbacks are temporary, not permanent
• Every small action counts
• You're building long-term habits, not seeking quick fixes

**🎯 Practical Strategies:**
• Break big goals into tiny daily actions
• Celebrate small wins (seriously!)
• Find accountability (friend, trainer, community)
• Track how you FEEL, not just numbers

**📈 Science Says:**
• It takes 21-66 days to form habits
• Consistency beats perfection every time
• Your brain adapts and makes things easier over time

**🚀 Next Steps:**
• What's ONE small thing you can do today?
• Focus on the process, not just outcomes
• Remember: you're stronger than you think!

What specific challenge is hitting you hardest right now? Let's tackle it together! 💪"""

    elif any(word in message_lower for word in ['sleep', 'tired', 'energy', 'fatigue', 'exhausted']):
        return f"""Hi {name}! Sleep is CRUCIAL for your health goals. Let's optimize your rest:

**😴 Sleep Science:**
• 7-9 hours for adults (recovery, hormone regulation)
• Deep sleep = muscle repair and growth hormone release
• Poor sleep = increased hunger hormones + decreased willpower

**🌙 Sleep Optimization Protocol:**
• Consistent bedtime/wake time (even weekends!)
• Dark, cool room (65-68°F/18-20°C)
• No screens 1 hour before bed
• Comfortable mattress and pillows

**☀️ Daytime Habits:**
• Morning sunlight exposure (10-30 minutes)
• Limit caffeine after 2 PM
• Regular exercise (but not 3 hours before bed)
• Manage stress through meditation/journaling

**🍵 Natural Sleep Aids:**
• Magnesium (200-400mg before bed)
• Chamomile tea
• Progressive muscle relaxation
• Reading or gentle stretching

**⚡ Energy Boosters:**
• Balanced meals (avoid sugar crashes)
• Stay hydrated throughout day
• Power naps (20 minutes max, before 3 PM)
• Regular movement breaks

What's your biggest sleep challenge? Falling asleep, staying asleep, or feeling tired despite sleep?"""

    else:
        # General helpful response
        goals_text = f"Your goals: {', '.join(user_profile.get('goals', []))}" if user_profile and user_profile.get('goals') else "your health journey"
        
        return f"""Hi {name}! I'm here to help with {goals_text}! 

**🎯 I can provide expert guidance on:**
• Personalized workout programs
• Evidence-based nutrition strategies
• Habit formation and psychology
• Sleep and recovery optimization
• Injury prevention and management
• Supplement recommendations
• Progress tracking methods

**💪 My approach combines:**
• Latest scientific research
• Practical, actionable advice
• Personalized recommendations
• Behavioral psychology insights

**🤔 Some questions I love helping with:**
• "Design a workout plan for my goals"
• "What should I eat to [specific goal]?"
• "How do I stay motivated long-term?"
• "Help me build better habits"
• "I'm plateauing, what should I change?"

What specific aspect of your health would you like to dive into? I'm excited to help you succeed! 🚀"""

def get_conversation_history(user_id):
    """Get recent conversation history"""
    if user_id and user_id in chat_history_db:
        return chat_history_db[user_id][-6:]  # Last 3 exchanges
    return []

def store_conversation(user_id, message, response):
    """Store conversation history"""
    if user_id:
        if user_id not in chat_history_db:
            chat_history_db[user_id] = []
        
        chat_history_db[user_id].extend([
            {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
        ])
        
        # Keep only last 20 messages
        if len(chat_history_db[user_id]) > 20:
            chat_history_db[user_id] = chat_history_db[user_id][-20:]

@app.route('/health_check')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'intelligent_v3.0',
        'ai_systems': {
            'openai_gpt': OPENAI_AVAILABLE,
            'rag_system': rag_system is not None,
            'fallback_system': True
        },
        'features': [
            'OpenAI GPT-3.5 Turbo',
            'Advanced RAG System', 
            'Comprehensive Health Metrics',
            'Evidence-Based Responses',
            'Conversation Memory',
            'Personalized Advice'
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting Intelligent BodyBae.ai...")
    print(f"🤖 OpenAI GPT: {'✅ Available' if OPENAI_AVAILABLE else '❌ Need API Key'}")
    print(f"🧠 RAG System: {'✅ Available' if rag_system else '❌ Fallback'}")
    print(f"💡 Smart Fallback: ✅ Available")
    print(f"🌐 Running on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)