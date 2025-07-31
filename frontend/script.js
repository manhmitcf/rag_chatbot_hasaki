// Hasaki Beauty AI Chatbot - Simplified Version
class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8002';
        this.sessionId = this.generateSessionId();
        this.messageCount = 0;
        this.productCount = 0;
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkApiStatus();
        this.updateStats();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearChat');
        this.apiStatus = document.getElementById('apiStatus');
        this.chatStats = document.getElementById('chatStats');
        this.quickActions = document.getElementById('quickActions');
        this.typingIndicator = document.getElementById('typingIndicator');
    }
    
    attachEventListeners() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.handleSendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateCharCount();
        });
        
        // Clear chat
        this.clearButton.addEventListener('click', () => this.clearChat());
        
        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.getAttribute('data-text');
                this.messageInput.value = text;
                this.handleSendMessage();
            });
        });
    }
    
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    updateCharCount() {
        const charCount = document.querySelector('.char-count');
        if (charCount) {
            const length = this.messageInput.value.length;
            charCount.textContent = `${length}/500`;
            charCount.style.color = length > 450 ? '#e74c3c' : '#666';
        }
    }
    
    async checkApiStatus() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                this.updateApiStatus('connected', 'Đã kết nối');
            } else {
                this.updateApiStatus('error', 'Lỗi kết nối');
            }
        } catch (error) {
            this.updateApiStatus('error', 'Không thể kết nối');
        }
    }
    
    updateApiStatus(status, text) {
        const statusDot = this.apiStatus.querySelector('.status-dot');
        const statusText = this.apiStatus.querySelector('span');
        
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
    
    updateStats() {
        const messageCountEl = this.chatStats.querySelector('.stat:first-child .stat-value');
        const productCountEl = this.chatStats.querySelector('.stat:last-child .stat-value');
        
        if (messageCountEl) messageCountEl.textContent = this.messageCount;
        if (productCountEl) productCountEl.textContent = this.productCount;
    }
    
    async handleSendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateCharCount();
        
        // Hide quick actions after first message
        if (this.quickActions) {
            this.quickActions.style.display = 'none';
        }
        
        // Show loading
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response
            this.addMessage('bot', data.answer);
            
            // Count products mentioned in response
            const productLinks = (data.answer.match(/\[.*?\]\(.*?\)/g) || []).length;
            this.productCount += productLinks;
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('bot', 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.');
        } finally {
            this.hideLoading();
            this.updateStats();
        }
    }
    
    addMessage(sender, content, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        // Create content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        if (typeof content === 'string') {
            messageText.innerHTML = MessageManager.formatMessage(content);
        } else {
            messageText.appendChild(content);
        }
        
        messageContent.appendChild(messageText);
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        messageContent.appendChild(timestamp);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.messageCount++;
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    showLoading() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
        }
    }
    
    hideLoading() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }
    
    clearChat() {
        // Keep welcome message, remove others
        const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(msg => msg.remove());
        
        // Reset stats
        this.messageCount = 0;
        this.productCount = 0;
        this.updateStats();
        
        // Show quick actions again
        if (this.quickActions) {
            this.quickActions.style.display = 'block';
        }
        
        // Generate new session
        this.sessionId = this.generateSessionId();
    }
}

// Message formatting utilities
class MessageManager {
    static formatMessage(text) {
        // Convert markdown-like formatting
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Convert markdown links to HTML links FIRST (before other link processing)
        text = MessageManager.formatMarkdownLinks(text);
        
        // Detect and convert URLs to clickable links
        text = MessageManager.formatLinks(text);
        
        // Detect and format product information
        if (text.includes('VND') || text.includes('đ')) {
            text = MessageManager.formatProductInfo(text);
        }
        
        return text;
    }
    
    static formatMarkdownLinks(text) {
        // Convert markdown links [text](url) to HTML links
        const markdownLinkPattern = /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/gi;
        
        return text.replace(markdownLinkPattern, (match, linkText, url) => {
            // Check if it's a Hasaki product link
            if (url.includes('hasaki.vn')) {
                return `<a href="${url}" target="_blank" class="markdown-product-link" title="Xem sản phẩm trên Hasaki" onclick="this.classList.add('clicked')">
                    <i class="fas fa-shopping-bag"></i>
                    <span>${linkText}</span>
                    <i class="fas fa-external-link-alt"></i>
                </a>`;
            } else {
                // General external link
                return `<a href="${url}" target="_blank" class="external-link markdown-external-link" title="Mở liên kết" onclick="this.classList.add('clicked')">
                    <i class="fas fa-link"></i>
                    <span>${linkText}</span>
                    <i class="fas fa-external-link-alt"></i>
                </a>`;
            }
        });
    }
    
    static formatLinks(text) {
        // Convert URLs to clickable links (skip if already in HTML tags)
        const urlPattern = /(?<!href=["'])(https?:\/\/[^\s<>"]+)/gi;
        return text.replace(urlPattern, (url) => {
            const displayUrl = MessageManager.truncateUrl(url);
            return `<a href="${url}" target="_blank" class="auto-link" title="${url}">
                <i class="fas fa-external-link-alt"></i>
                ${displayUrl}
            </a>`;
        });
    }
    
    static truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }
    
    static formatProductInfo(text) {
        // Format price information
        text = text.replace(/(\d{1,3}(?:\.\d{3})*)\s*(VND|đ)/gi, 
            '<span class="price-highlight">$1 $2</span>');
        
        // Format discount information
        text = text.replace(/(giảm|sale|khuyến mãi)\s*(\d+)%/gi, 
            '<span class="discount-highlight">$1 $2%</span>');
        
        return text;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

// Add some utility functions
window.ChatUtils = {
    copyToClipboard: (text) => {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Copied to clipboard');
        });
    },
    
    shareMessage: (message) => {
        if (navigator.share) {
            navigator.share({
                title: 'Hasaki Beauty AI',
                text: message
            });
        }
    }
};