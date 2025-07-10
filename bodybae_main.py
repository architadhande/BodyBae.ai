import os
import streamlit as st
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from rag import RAGSystem
import plotly.graph_objects as go
import plotly.express as px

# Page config with matcha theme
st.set_page_config(
    page_title="BodyBae - Your Health Assistant",
    page_icon="🍵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for matcha theme
st.markdown("""
<style>
    /* Main theme colors - Matcha palette */
    :root {
        --matcha-dark: #2d4a2b;
        --matcha-medium: #4a7c47;
        --matcha-light: #8bc34a;
        --matcha-cream: #f1f8e9;
        --matcha-accent: #689f38;
    }
    
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #4a7c47 0%, #689f38 100%);
        color: white;
        padding: 15px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        max-width: 70%;
        margin-left: auto;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: white;
        color: #2d4a2b;
        padding: 15px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        max-width: 70%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        border: 1px solid #e8f5e9;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #2d4a2b 0%, #4a7c47 100%);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #689f38 0%, #8bc34a 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(104, 159, 56, 0.3);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #8bc34a;
        padding: 10px 15px;
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #689f38;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2d4a2b;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem()
if 'goals' not in st.session_state:
    st.session_state.goals = []

# Load or initialize user data
def load_user_data():
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open('user_data.json', 'w') as f:
        json.dump(data, f)

# BMI Calculator
def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)"""
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
        color = "#ff9800"
    elif 18.5 <= bmi < 25:
        category = "Normal weight"
        color = "#4caf50"
    elif 25 <= bmi < 30:
        category = "Overweight"
        color = "#ff9800"
    else:
        category = "Obese"
        color = "#f44336"
    
    return bmi, category, color

# Sidebar for user profile and BMI
with st.sidebar:
    st.markdown("# 🍵 BodyBae")
    st.markdown("### Your Health & Wellness Assistant")
    
    # User Profile Section
    st.markdown("---")
    st.markdown("### 👤 User Profile")
    
    if not st.session_state.user_profile:
        with st.form("profile_form"):
            name = st.text_input("Name", placeholder="Enter your name")
            age = st.number_input("Age", min_value=1, max_value=120, value=25)
            weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
            height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
            
            submitted = st.form_submit_button("Save Profile")
            
            if submitted and name:
                st.session_state.user_profile = {
                    'name': name,
                    'age': age,
                    'weight': weight,
                    'height': height,
                    'created_at': datetime.now().isoformat()
                }
                save_user_data(st.session_state.user_profile)
                st.rerun()
    else:
        # Display profile
        profile = st.session_state.user_profile
        st.markdown(f"**Name:** {profile['name']}")
        st.markdown(f"**Age:** {profile['age']} years")
        st.markdown(f"**Weight:** {profile['weight']} kg")
        st.markdown(f"**Height:** {profile['height']} cm")
        
        # Calculate and display BMI
        bmi, category, color = calculate_bmi(profile['weight'], profile['height'])
        
        st.markdown("---")
        st.markdown("### 📊 BMI Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("BMI", f"{bmi:.1f}")
        with col2:
            st.markdown(f"<p style='color: {color}; font-weight: bold;'>{category}</p>", 
                       unsafe_allow_html=True)
        
        # BMI Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = bmi,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "BMI Score"},
            gauge = {
                'axis': {'range': [None, 40]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 18.5], 'color': "#ffebee"},
                    {'range': [18.5, 25], 'color': "#e8f5e9"},
                    {'range': [25, 30], 'color': "#fff3e0"},
                    {'range': [30, 40], 'color': "#ffebee"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 25
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Update profile button
        if st.button("Update Profile"):
            for key in ['user_profile', 'goals']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Goals Section
    st.markdown("---")
    st.markdown("### 🎯 Health Goals")
    
    if st.session_state.user_profile:
        # Add new goal
        new_goal = st.text_input("Add a new goal", placeholder="e.g., Lose 5kg in 3 months")
        if st.button("Add Goal") and new_goal:
            st.session_state.goals.append({
                'goal': new_goal,
                'created_at': datetime.now().isoformat(),
                'completed': False
            })
        
        # Display goals
        for i, goal in enumerate(st.session_state.goals):
            col1, col2 = st.columns([3, 1])
            with col1:
                if goal['completed']:
                    st.markdown(f"~~{goal['goal']}~~ ✅")
                else:
                    st.markdown(f"• {goal['goal']}")
            with col2:
                if not goal['completed']:
                    if st.button("✓", key=f"complete_{i}"):
                        st.session_state.goals[i]['completed'] = True
                        st.rerun()

# Main chat interface
st.markdown("## 💬 Chat with BodyBae")
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"<div class='user-message'>{message['content']}</div>", 
                   unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='assistant-message'>{message['content']}</div>", 
                   unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Chat input
with st.container():
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Ask me anything about health, fitness, or nutrition...", 
                                  key="user_input", 
                                  placeholder="Type your message here...")
    with col2:
        send_button = st.button("Send 🍵")

# Process user input
if (user_input and send_button) or (user_input and st.session_state.get('enter_pressed', False)):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate response using RAG
    with st.spinner("Thinking... 🍵"):
        # Add context about user profile if available
        context = ""
        if st.session_state.user_profile:
            profile = st.session_state.user_profile
            bmi, category, _ = calculate_bmi(profile['weight'], profile['height'])
            context = f"User Profile: {profile['name']}, {profile['age']} years old, "
            context += f"Weight: {profile['weight']}kg, Height: {profile['height']}cm, "
            context += f"BMI: {bmi:.1f} ({category}). "
            
            if st.session_state.goals:
                active_goals = [g['goal'] for g in st.session_state.goals if not g['completed']]
                if active_goals:
                    context += f"Current goals: {', '.join(active_goals)}. "
        
        # Get response from RAG system
        response = st.session_state.rag_system.get_response(user_input, context)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clear input and rerun
    st.rerun()

# Footer with health tips
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 💧 Hydration Tip")
    st.markdown("Drink at least 8 glasses of water daily for optimal health.")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 🏃 Activity Tip")
    st.markdown("Aim for 30 minutes of moderate exercise 5 days a week.")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### 🥗 Nutrition Tip")
    st.markdown("Include 5 servings of fruits and vegetables in your daily diet.")
    st.markdown("</div>", unsafe_allow_html=True)
