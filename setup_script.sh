#!/bin/bash

# Create necessary directories
mkdir -p .streamlit

# Download the model cache to speed up loading
echo "Setting up model cache..."
python -c "
from transformers import AutoTokenizer, AutoModel
print('Downloading model...')
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
print('Model downloaded successfully!')
"

echo "Setup complete!"