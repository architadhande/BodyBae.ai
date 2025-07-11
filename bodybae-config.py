import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///bodybae.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Goal settings
    WEIGHT_LOSS_RATE_PER_WEEK = 1.5  # pounds
    WEIGHT_GAIN_RATE_PER_WEEK = 1.0  # pounds
    MUSCLE_GAIN_RATE_PER_MONTH = 2.0  # pounds
    FAT_LOSS_RATE_PER_WEEK = 1.0  # pounds