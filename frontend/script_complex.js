// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8002',
    MAX_MESSAGE_LENGTH: 500,
    TYPING_DELAY: 1000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 2000,
    HASAKI_BASE_URL: 'https://hasaki.vn'
};

// State Management
class ChatState {
    constructor() {
        this.isConnected = false;
        this.isTyping = false;
        this.messageCount = 0;
        this.productCount = 0;
        this.currentRetryAttempt = 0;
        this.lastMessage = '';
    }

    updateStats() {
        document.getElementById('chatStats').innerHTML = `
            <div class="stat">
                <span class="stat-value">${this.messageCount}</span>
                <span class="stat-label">Tin nhắn</span>
            </div>
            <div class="stat">
                <span class="stat-value">${this.productCount}</span>
                <span class="stat-label">Sản phẩm tư vấn</span>
            </div>
        `;
    }

    setConnected(connected) {
        this.isConnected = connected;
        const statusIndicator = document.getElementById('apiStatus');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('span');

        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Đã kết nối';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Mất kết nối';
        }
    }
}

// Initialize state
const chatState = new ChatState();

// DOM Elements
const elements = {
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    chatMessages: document.getElementById('chatMessages'),
    clearChatButton: document.getElementById('clearChat'),
    quickActions: document.getElementById('quickActions'),
    errorModal: document.getElementById('errorModal'),
    typingIndicator: document.getElementById('typingIndicator'),
    charCount: document.querySelector('.char-count')
};

// API Service
class APIService {
    static async checkHealth() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    static async sendMessage(message) {
        const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: 'web_session_' + Date.now(),
                show_details: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    static async clearMemory() {
        const response = await fetch(`${CONFIG.API_BASE_URL}/memory/clear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }
}

// Message Management
class MessageManager {
    static addMessage(content, isUser = false, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
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
        
        // Add product links if metadata contains product info
        if (metadata && (metadata.id_product || metadata.name_product)) {
            const productLinks = MessageManager.createProductLinks(metadata);
            if (productLinks) {
                messageContent.appendChild(productLinks);
            }
        }
        
        // Add metadata if available
        if (metadata) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            
            const timeSpan = document.createElement('span');
            timeSpan.textContent = new Date().toLocaleTimeString('vi-VN', {
                hour: '2-digit',
                minute: '2-digit'
            });
            metaDiv.appendChild(timeSpan);
            
            if (metadata.processing_time) {
                const timeInfo = document.createElement('span');
                timeInfo.innerHTML = `<i class="fas fa-clock"></i> ${metadata.processing_time.toFixed(1)}s`;
                metaDiv.appendChild(timeInfo);
            }
            
            if (metadata.documents_found) {
                const docsInfo = document.createElement('span');
                docsInfo.innerHTML = `<i class="fas fa-database"></i> ${metadata.documents_found} tài liệu`;
                metaDiv.appendChild(docsInfo);
            }
            
            messageContent.appendChild(metaDiv);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        elements.chatMessages.appendChild(messageDiv);
        MessageManager.scrollToBottom();
        
        // Update stats
        chatState.messageCount++;
        if (!isUser && metadata && metadata.id_product) {
            chatState.productCount++;
        }
        chatState.updateStats();
    }

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
                return `<a href="${url}" target="_blank" class="product-link markdown-product-link" title="Xem sản phẩm trên Hasaki" onclick="this.classList.add('clicked')">
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
        // Regex patterns for different types of links (skip already processed markdown links)
        const patterns = {
            // Hasaki product URLs (not already in HTML)
            hasaki: /(?<!href=["'])https?:\/\/(www\.)?hasaki\.vn\/[^\s<>]+/gi,
            // General URLs (not already in HTML)
            general: /(?<!href=["'])https?:\/\/[^\s<>]+/gi,
            // Product IDs (convert to Hasaki links)
            productId: /(?:Mã sản phẩm|Product ID|ID):\s*([A-Z0-9]+)/gi
        };

        // Format Hasaki product links (only if not already processed)
        text = text.replace(patterns.hasaki, (url) => {
            return `<a href="${url}" target="_blank" class="product-link hasaki-link" title="Xem sản phẩm trên Hasaki" onclick="this.classList.add('clicked')">
                <i class="fas fa-external-link-alt"></i>
                Xem sản phẩm trên Hasaki
            </a>`;
        });

        // Format general URLs (but not already formatted links)
        text = text.replace(patterns.general, (url) => {
            if (url.includes('hasaki.vn') && text.includes('class="product-link')) {
                return url; // Skip if already formatted as Hasaki link
            }
            return `<a href="${url}" target="_blank" class="external-link" title="Mở liên kết" onclick="this.classList.add('clicked')">
                <i class="fas fa-link"></i>
                ${MessageManager.truncateUrl(url)}
            </a>`;
        });

        // Convert product IDs to Hasaki links
        text = text.replace(patterns.productId, (match, productId) => {
            const hasakiUrl = `${CONFIG.HASAKI_BASE_URL}/san-pham/${productId.toLowerCase()}`;
            return `${match} <a href="${hasakiUrl}" target="_blank" class="product-link product-id-link" title="Xem sản phẩm" onclick="this.classList.add('clicked')">
                <i class="fas fa-shopping-bag"></i>
                Xem sản phẩm
            </a>`;
        });

        return text;
    }

    static truncateUrl(url) {
        if (url.length > 50) {
            return url.substring(0, 47) + '...';
        }
        return url;
    }

    static createProductLinks(metadata) {
        if (!metadata.id_product && !metadata.name_product) {
            return null;
        }

        const linksContainer = document.createElement('div');
        linksContainer.className = 'product-links';

        // Create main product link
        if (metadata.id_product) {
            const productUrl = `${CONFIG.HASAKI_BASE_URL}/san-pham/${metadata.id_product}`;
            const mainLink = document.createElement('a');
            mainLink.href = productUrl;
            mainLink.target = '_blank';
            mainLink.className = 'product-link main-product-link';
            mainLink.title = 'Xem chi tiết sản phẩm';
            mainLink.onclick = () => mainLink.classList.add('clicked');
            mainLink.innerHTML = `
                <i class="fas fa-shopping-bag"></i>
                <span>Xem sản phẩm: ${metadata.name_product || 'Chi tiết'}</span>
                <i class="fas fa-external-link-alt"></i>
            `;
            linksContainer.appendChild(mainLink);
        }

        // Create additional action links
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'product-actions';

        // Search similar products
        const searchLink = document.createElement('a');
        searchLink.href = `${CONFIG.HASAKI_BASE_URL}/tim-kiem?q=${encodeURIComponent(metadata.name_product || '')}`;
        searchLink.target = '_blank';
        searchLink.className = 'action-link search-link';
        searchLink.title = 'Tìm sản phẩm tương tự';
        searchLink.onclick = () => searchLink.classList.add('clicked');
        searchLink.innerHTML = `
            <i class="fas fa-search"></i>
            Tìm tương tự
        `;
        actionsContainer.appendChild(searchLink);

        // Compare products
        const compareLink = document.createElement('button');
        compareLink.className = 'action-link compare-link';
        compareLink.title = 'So sánh sản phẩm';
        compareLink.innerHTML = `
            <i class="fas fa-balance-scale"></i>
            So sánh
        `;
        compareLink.onclick = () => MessageManager.handleCompareProduct(metadata);
        actionsContainer.appendChild(compareLink);

        // Add to wishlist
        const wishlistLink = document.createElement('button');
        wishlistLink.className = 'action-link wishlist-link';
        wishlistLink.title = 'Thêm vào danh sách yêu thích';
        wishlistLink.innerHTML = `
            <i class="fas fa-heart"></i>
            Yêu thích
        `;
        wishlistLink.onclick = () => MessageManager.handleAddToWishlist(metadata);
        actionsContainer.appendChild(wishlistLink);

        linksContainer.appendChild(actionsContainer);

        return linksContainer;
    }

    static handleCompareProduct(metadata) {
        // Store product for comparison
        const compareData = {
            id: metadata.id_product,
            name: metadata.name_product,
            timestamp: Date.now()
        };
        
        // Save to localStorage
        let compareList = JSON.parse(localStorage.getItem('hasaki_compare') || '[]');
        
        // Check if already in compare list
        if (!compareList.find(item => item.id === compareData.id)) {
            compareList.push(compareData);
            
            // Limit to 3 products for comparison
            if (compareList.length > 3) {
                compareList = compareList.slice(-3);
            }
            
            localStorage.setItem('hasaki_compare', JSON.stringify(compareList));
            
            // Show notification
            MessageManager.showNotification(`Đã thêm "${metadata.name_product}" vào danh sách so sánh`, 'success');
        } else {
            MessageManager.showNotification('Sản phẩm đã có trong danh sách so sánh', 'info');
        }
    }

    static handleAddToWishlist(metadata) {
        // Store product in wishlist
        const wishlistData = {
            id: metadata.id_product,
            name: metadata.name_product,
            timestamp: Date.now()
        };
        
        // Save to localStorage
        let wishlist = JSON.parse(localStorage.getItem('hasaki_wishlist') || '[]');
        
        // Check if already in wishlist
        if (!wishlist.find(item => item.id === wishlistData.id)) {
            wishlist.push(wishlistData);
            localStorage.setItem('hasaki_wishlist', JSON.stringify(wishlist));
            
            // Show notification
            MessageManager.showNotification(`Đã thêm "${metadata.name_product}" vào danh sách yêu thích`, 'success');
        } else {
            MessageManager.showNotification('Sản phẩm đã có trong danh sách yêu thích', 'info');
        }
    }

    static showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto hide after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);

        // Close button
        notification.querySelector('.notification-close').onclick = () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        };
    }

    static formatProductInfo(text) {
        // Try to extract product information and format it nicely
        const lines = text.split('<br>');
        let formattedText = '';
        let inProductSection = false;
        
        for (let line of lines) {
            if (line.includes('Tên sản phẩm:') || line.includes('Sản phẩm:')) {
                inProductSection = true;
                formattedText += '<div class="product-info">';
            }
            
            if (inProductSection && (line.includes('Giá:') || line.includes('VND'))) {
                line = line.replace(/([\d,]+\s*VND)/g, '<span class="product-price">$1</span>');
            }
            
            formattedText += line + '<br>';
            
            if (inProductSection && line.trim() === '') {
                formattedText += '</div>';
                inProductSection = false;
            }
        }
        
        if (inProductSection) {
            formattedText += '</div>';
        }
        
        return formattedText;
    }

    static scrollToBottom() {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    static showTyping() {
        chatState.isTyping = true;
        elements.typingIndicator.classList.add('active');
    }

    static hideTyping() {
        chatState.isTyping = false;
        elements.typingIndicator.classList.remove('active');
    }
}

// Loading Management
class LoadingManager {
    static show(message = 'Đang xử lý câu hỏi của bạn') {
        // Just show typing indicator instead of full overlay
        MessageManager.showTyping();
    }

    static hide() {
        // Just hide typing indicator
        MessageManager.hideTyping();
    }
}

// Error Management
class ErrorManager {
    static show(message, error = null) {
        document.getElementById('errorMessage').textContent = message;
        elements.errorModal.classList.add('active');
        
        if (error) {
            console.error('Error details:', error);
        }
    }

    static hide() {
        elements.errorModal.classList.remove('active');
    }

    static handleAPIError(error) {
        let message = 'Đã xảy ra lỗi khi kết nối với server.';
        
        if (error.message.includes('timeout')) {
            message = 'Kết nối bị timeout. Vui lòng thử lại.';
        } else if (error.message.includes('503')) {
            message = 'Server đang bảo trì. Vui lòng thử lại sau.';
        } else if (error.message.includes('500')) {
            message = 'Lỗi server nội bộ. Vui lòng thử lại.';
        }
        
        this.show(message, error);
    }
}

// Main Chat Functions
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    
    if (!message || chatState.isTyping) {
        return;
    }
    
    if (!chatState.isConnected) {
        ErrorManager.show('Không thể kết nối đến server. Vui lòng kiểm tra kết nối.');
        return;
    }
    
    // Store message for retry
    chatState.lastMessage = message;
    
    // Add user message
    MessageManager.addMessage(message, true);
    
    // Clear input
    elements.messageInput.value = '';
    updateCharCount();
    
    // Hide quick actions after first message
    if (elements.quickActions.style.display !== 'none') {
        elements.quickActions.style.display = 'none';
    }
    
    // Show loading and typing
    LoadingManager.show();
    MessageManager.showTyping();
    
    try {
        const response = await APIService.sendMessage(message);
        
        LoadingManager.hide();
        MessageManager.hideTyping();
        
        if (response.success) {
            MessageManager.addMessage(response.answer, false, {
                processing_time: response.processing_time,
                documents_found: response.documents_found,
                id_product: response.id_product,
                name_product: response.name_product,
                route: response.route
            });
            
            // Reset retry attempts on success
            chatState.currentRetryAttempt = 0;
        } else {
            throw new Error(response.error || 'Unknown error');
        }
        
    } catch (error) {
        LoadingManager.hide();
        MessageManager.hideTyping();
        
        console.error('Send message error:', error);
        
        // Auto retry logic
        if (chatState.currentRetryAttempt < CONFIG.RETRY_ATTEMPTS) {
            chatState.currentRetryAttempt++;
            
            MessageManager.addMessage(
                `⚠️ Lỗi kết nối. Đang thử lại lần ${chatState.currentRetryAttempt}/${CONFIG.RETRY_ATTEMPTS}...`,
                false
            );
            
            setTimeout(() => {
                sendMessage();
            }, CONFIG.RETRY_DELAY);
        } else {
            ErrorManager.handleAPIError(error);
            chatState.currentRetryAttempt = 0;
        }
    }
}

async function clearChat() {
    if (!confirm('Bạn có chắc muốn xóa toàn bộ lịch sử hội thoại?')) {
        return;
    }
    
    try {
        await APIService.clearMemory();
        
        // Clear messages except welcome message
        const messages = elements.chatMessages.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(msg => msg.remove());
        
        // Reset stats
        chatState.messageCount = 0;
        chatState.productCount = 0;
        chatState.updateStats();
        
        // Show quick actions again
        elements.quickActions.style.display = 'block';
        
        MessageManager.addMessage('✅ Đã xóa lịch sử hội thoại. Bạn có thể bắt đầu cuộc trò chuyện mới!', false);
        
    } catch (error) {
        ErrorManager.handleAPIError(error);
    }
}

function updateCharCount() {
    const length = elements.messageInput.value.length;
    elements.charCount.textContent = `${length}/${CONFIG.MAX_MESSAGE_LENGTH}`;
    
    if (length > CONFIG.MAX_MESSAGE_LENGTH * 0.9) {
        elements.charCount.style.color = 'var(--error-color)';
    } else {
        elements.charCount.style.color = 'var(--gray-500)';
    }
}

function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
}

async function checkAPIConnection() {
    const isConnected = await APIService.checkHealth();
    chatState.setConnected(isConnected);
    
    if (!isConnected) {
        setTimeout(checkAPIConnection, 5000); // Retry every 5 seconds
    }
}

// Event Listeners
function setupEventListeners() {
    // Send message
    elements.sendButton.addEventListener('click', sendMessage);
    
    // Enter key to send
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto resize textarea
    elements.messageInput.addEventListener('input', () => {
        updateCharCount();
        autoResizeTextarea();
    });
    
    // Character count
    elements.messageInput.addEventListener('input', updateCharCount);
    
    // Clear chat
    elements.clearChatButton.addEventListener('click', clearChat);
    
    // Quick action buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('quick-btn') || e.target.closest('.quick-btn')) {
            const button = e.target.classList.contains('quick-btn') ? e.target : e.target.closest('.quick-btn');
            const text = button.getAttribute('data-text');
            elements.messageInput.value = text;
            updateCharCount();
            autoResizeTextarea();
            elements.messageInput.focus();
        }
    });
    
    // Error modal
    document.getElementById('closeErrorModal').addEventListener('click', () => {
        ErrorManager.hide();
    });
    
    document.getElementById('retryButton').addEventListener('click', () => {
        ErrorManager.hide();
        if (chatState.lastMessage) {
            elements.messageInput.value = chatState.lastMessage;
            sendMessage();
        }
    });
    
    document.getElementById('contactSupport').addEventListener('click', () => {
        window.open('mailto:support@hasaki.vn?subject=Chatbot Support Request', '_blank');
    });
    
    // Close modal on outside click
    elements.errorModal.addEventListener('click', (e) => {
        if (e.target === elements.errorModal) {
            ErrorManager.hide();
        }
    });
    
    // Prevent form submission
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
        }
    });
}

// Initialize Application
function initializeApp() {
    console.log('🌸 Hasaki Beauty AI Chatbot initialized with clickable product links');
    
    // Setup event listeners
    setupEventListeners();
    
    // Check API connection
    checkAPIConnection();
    
    // Set initial focus
    elements.messageInput.focus();
    
    // Initialize stats
    chatState.updateStats();
    
    // Add welcome animation
    setTimeout(() => {
        document.querySelector('.welcome-message').classList.add('fade-in');
    }, 500);
}

// Start the application when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    ErrorManager.show('Đã xảy ra lỗi không mong muốn. Vui lòng tải lại trang.');
});

// Handle online/offline status
window.addEventListener('online', () => {
    checkAPIConnection();
});

window.addEventListener('offline', () => {
    chatState.setConnected(false);
    ErrorManager.show('Mất kết nối internet. Vui lòng kiểm tra kết nối của bạn.');
});