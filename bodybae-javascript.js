// BodyBae.ai Chat Interface

class BodyBaeChat {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.modal = document.getElementById('user-form-modal');
        this.userProfileForm = document.getElementById('user-profile-form');
        this.actionButtons = document.querySelectorAll('.action-button');
        
        this.userId = localStorage.getItem('bodybae_user_id');
        this.userName = localStorage.getItem('bodybae_user_name');
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Quick action buttons
        this.actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handleQuickAction(action);
            });
        });
        
        // User profile form
        this.userProfileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitUserProfile();
        });
        
        // Focus on input
        this.userInput.focus();
    }
    
    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.userInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.userId
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Handle response based on type
            this.handleResponse(data);
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            console.error('Error:', error);
        }
    }
    
    handleResponse(data) {
        switch (data.type) {
            case 'onboarding':
                this.addMessage(data.message, 'bot');
                if (data.step === 'welcome') {
                    setTimeout(() => this.showUserForm(), 1000);
                }
                break;
                
            case 'goal_setting':
                this.addMessage(data.message, 'bot');
                if (data.options) {
                    this.addOptionsButtons(data.options);
                }
                break;
                
            case 'progress_logging':
                this.addMessage(data.message, 'bot');
                if (data.options) {
                    this.addOptionsButtons(data.options);
                }
                break;
                
            case 'chat':
            default:
                this.addMessage(data.message, 'bot');
                break;
        }
        
        // Store user_id if provided
        if (data.user_id) {
            this.userId = data.user_id;
            localStorage.setItem('bodybae_user_id', data.user_id);
        }
    }
    
    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'bot' ? '🤖' : '👤';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = this.formatMessage(content);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Convert markdown-style formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    addOptionsButtons(options) {
        const optionsDiv = document.createElement('div');
        optionsDiv.className = 'message bot-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const optionsContent = document.createElement('div');
        optionsContent.className = 'message-content quick-options';
        
        options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'option-button';
            button.textContent = option;
            button.onclick = () => {
                this.userInput.value = option;
                this.sendMessage();
            };
            optionsContent.appendChild(button);
        });
        
        optionsDiv.appendChild(avatar);
        optionsDiv.appendChild(optionsContent);
        this.chatMessages.appendChild(optionsDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-message';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingMessage = document.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showUserForm() {
        this.modal.style.display = 'block';
    }
    
    hideUserForm() {
        this.modal.style.display = 'none';
    }
    
    async submitUserProfile() {
        const formData = new FormData(this.userProfileForm);
        const userData = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/api/user/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.userId = data.user_id;
                this.userName = userData.name;
                localStorage.setItem('bodybae_user_id', data.user_id);
                localStorage.setItem('bodybae_user_name', userData.name);
                
                this.hideUserForm();
                this.addMessage(data.message, 'bot');
                
                // Prompt for goals
                setTimeout(() => {
                    this.userInput.value = "I want to set my fitness goals";
                    this.sendMessage();
                }, 1500);
            }
        } catch (error) {
            console.error('Error submitting profile:', error);
            alert('Error creating profile. Please try again.');
        }
    }
    
    async handleQuickAction(action) {
        switch (action) {
            case 'goals':
                this.userInput.value = "I want to set my fitness goals";
                this.sendMessage();
                break;
                
            case 'progress':
                this.userInput.value = "I want to log my progress";
                this.sendMessage();
                break;
                
            case 'tip':
                await this.getDailyTip();
                break;
                
            case 'faq':
                this.userInput.value = "I have a health question";
                this.sendMessage();
                break;
        }
    }
    
    async getDailyTip() {
        this.showTypingIndicator();
        
        try {
            const response = await fetch(`/api/tips/daily?user_id=${this.userId}`);
            const data = await response.json();
            
            this.hideTypingIndicator();
            this.addMessage(`💡 Daily Tip: ${data.tip}`, 'bot');
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Unable to fetch daily tip. Please try again.', 'bot');
        }
    }
}

// Style additions for options buttons
const style = document.createElement('style');
style.textContent = `
    .quick-options {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .option-button {
        padding: 8px 16px;
        background-color: var(--matcha-light);
        color: white;
        border: none;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .option-button:hover {
        background-color: var(--matcha-medium);
        transform: scale(1.05);
    }
    
    .option-button:active {
        transform: scale(0.95);
    }
`;
document.head.appendChild(style);

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BodyBaeChat();
});
