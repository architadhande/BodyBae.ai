from flask import Flask, request, jsonify, session
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Simple storage
users_db = {}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BodyBae.ai - Debug Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #A4B07E, #707C4F);
                color: white;
                margin: 0;
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 2rem; 
            }
            .welcome { 
                text-align: center; 
                padding: 4rem 2rem;
                display: block;
            }
            .chat { 
                display: none; 
                background: white;
                color: #424106;
                border-radius: 10px;
                padding: 2rem;
                margin-top: 2rem;
            }
            button { 
                background: #C6A6B5; 
                color: white; 
                border: none; 
                padding: 1rem 2rem; 
                border-radius: 50px; 
                cursor: pointer; 
                font-size: 1.1rem;
                margin: 0.5rem;
            }
            button:hover { 
                background: #6D4930; 
            }
            .form-group {
                margin: 1rem 0;
            }
            input, select {
                width: 100%;
                padding: 0.5rem;
                margin: 0.3rem 0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .chat-area {
                border: 1px solid #ddd;
                padding: 1rem;
                height: 300px;
                overflow-y: auto;
                margin: 1rem 0;
                background: #f9f9f9;
            }
            .message {
                margin: 0.5rem 0;
                padding: 0.5rem;
                border-radius: 5px;
            }
            .user { background: #A4B07E; color: white; text-align: right; }
            .bot { background: #e0e0e0; color: #424106; }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Welcome Section -->
            <div id="welcome" class="welcome">
                <h1 style="font-size: 3rem; margin-bottom: 1rem; color: #424106;">BodyBae.ai</h1>
                <p style="font-size: 1.5rem; margin-bottom: 2rem;">AI Health & Fitness Chatbot</p>
                <button onclick="showChat()">Start Chatting</button>
                <button onclick="testFunction()">Test Button</button>
                <div id="debug" style="margin-top: 1rem; font-size: 0.9rem;"></div>
            </div>

            <!-- Chat Section -->
            <div id="chat" class="chat">
                <h2>🤖 BodyBae Chat</h2>
                
                <!-- User Profile -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <h3>Your Profile</h3>
                        <div class="form-group">
                            <label>Name:</label>
                            <input type="text" id="name" placeholder="Your name">
                        </div>
                        <div class="form-group">
                            <label>Age:</label>
                            <input type="number" id="age" min="13" max="100" placeholder="25">
                        </div>
                        <div class="form-group">
                            <label>Height (cm):</label>
                            <input type="number" id="height" min="100" max="250" placeholder="170">
                        </div>
                        <div class="form-group">
                            <label>Weight (kg):</label>
                            <input type="number" id="weight" min="30" max="300" placeholder="70">
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
                        <div class="form-group">
                            <label>Activity Level:</label>
                            <select id="activity">
                                <option value="">Select</option>
                                <option value="sedentary">Sedentary</option>
                                <option value="lightly_active">Lightly Active</option>
                                <option value="moderately_active">Moderately Active</option>
                                <option value="very_active">Very Active</option>
                            </select>
                        </div>
                        <button onclick="calculateBMI()">Calculate BMI</button>
                        <div id="bmi-result" style="margin-top: 1rem; padding: 1rem; background: #f0f0f0; border-radius: 5px;"></div>
                    </div>

                    <div>
                        <h3>Chat with BodyBae</h3>
                        <div id="messages" class="chat-area">
                            <div class="message bot">Hi! I'm BodyBae. Fill out your profile and I'll give you personalized health advice!</div>
                        </div>
                        <div style="display: flex; gap: 0.5rem;">
                            <input type="text" id="message-input" placeholder="Ask me about health, fitness, nutrition..." style="flex: 1;">
                            <button onclick="sendMessage()">Send</button>
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <button onclick="sendQuickMessage('I want to lose weight')">Weight Loss</button>
                            <button onclick="sendQuickMessage('Help me build muscle')">Build Muscle</button>
                            <button onclick="sendQuickMessage('Give me a workout plan')">Workout Plan</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Debug function
            function testFunction() {
                document.getElementById('debug').innerHTML = 'JavaScript is working! ✅';
                console.log('Test function called');
            }

            // Show chat function
            function showChat() {
                console.log('showChat called');
                document.getElementById('debug').innerHTML = 'Switching to chat... ⏳';
                
                document.getElementById('welcome').style.display = 'none';
                document.getElementById('chat').style.display = 'block';
                
                console.log('Chat should be visible now');
                setTimeout(() => {
                    document.getElementById('debug').innerHTML = '';
                }, 2000);
            }

            // BMI calculation
            async function calculateBMI() {
                const name = document.getElementById('name').value;
                const age = document.getElementById('age').value;
                const height = document.getElementById('height').value;
                const weight = document.getElementById('weight').value;
                const gender = document.getElementById('gender').value;
                const activity = document.getElementById('activity').value;

                if (!name || !age || !height || !weight || !gender || !activity) {
                    alert('Please fill in all fields');
                    return;
                }

                try {
                    const response = await fetch('/calculate_bmi', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name, age: parseInt(age), height: parseFloat(height), 
                            weight: parseFloat(weight), gender, activity
                        })
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('bmi-result').innerHTML = `
                            <strong>BMI: ${result.bmi}</strong><br>
                            Category: ${result.category}<br>
                            ${result.advice}
                        `;
                        
                        addMessage('bot', `Great! Your BMI is ${result.bmi} (${result.category}). I'm ready to help with personalized advice!`);
                    } else {
                        alert('Error calculating BMI');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Network error');
                }
            }

            // Send message
            async function sendMessage() {
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                
                if (!message) return;

                addMessage('user', message);
                input.value = '';

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });

                    const result = await response.json();
                    addMessage('bot', result.response);
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('bot', 'Sorry, I had trouble responding. Please try again!');
                }
            }

            // Quick message
            function sendQuickMessage(message) {
                document.getElementById('message-input').value = message;
                sendMessage();
            }

            // Add message to chat
            function addMessage(sender, message) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                messageDiv.textContent = message;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            // Enter key support
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            console.log('Script loaded successfully');
        </script>
    </body>
    </html>
    '''

@app.route('/calculate_bmi', methods=['POST'])
def calculate_bmi():
    data = request.json
    try:
        weight = data['weight']
        height = data['height'] / 100  # Convert to meters
        bmi = weight / (height ** 2)
        
        if bmi < 18.5:
            category = "Underweight"
            advice = "Consider focusing on healthy weight gain."
        elif bmi < 25:
            category = "Normal Weight"
            advice = "Great job maintaining a healthy weight!"
        elif bmi < 30:
            category = "Overweight"
            advice = "Consider a moderate weight loss approach."
        else:
            category = "Obese"
            advice = "Consult healthcare professionals for guidance."
        
        return jsonify({
            'success': True,
            'bmi': round(bmi, 1),
            'category': category,
            'advice': advice
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '')
    
    # Simple responses
    message_lower = message.lower()
    
    if 'weight loss' in message_lower or 'lose weight' in message_lower:
        response = "For healthy weight loss, create a moderate caloric deficit through balanced nutrition and regular exercise. Focus on whole foods and stay consistent! 💪"
    elif 'muscle' in message_lower or 'build muscle' in message_lower:
        response = "To build muscle: eat adequate protein (1.6-2.2g per kg body weight), focus on progressive overload, and get plenty of sleep for recovery! 🏋️‍♀️"
    elif 'workout' in message_lower or 'exercise' in message_lower:
        response = "For effective workouts, combine strength training with cardio, focus on compound movements, and aim for consistency over perfection! 🌟"
    elif 'nutrition' in message_lower or 'food' in message_lower or 'eat' in message_lower:
        response = "Focus on whole foods: lean proteins, vegetables, fruits, whole grains, and healthy fats. Stay hydrated and eat balanced meals! 🥗"
    else:
        response = "I'm here to help with your health and fitness journey! Ask me about nutrition, workouts, weight management, or motivation. What would you like to know? 😊"
    
    return jsonify({'response': response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
