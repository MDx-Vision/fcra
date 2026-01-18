/**
 * AI Chat Widget for Client Portal
 * Provides Claude-powered chat support with escalation to staff
 */

(function() {
    'use strict';

    // State
    let conversationId = null;
    let isOpen = false;
    let isLoading = false;
    let isEscalated = false;

    // DOM Elements (populated on init)
    let widget = null;
    let chatWindow = null;
    let messagesContainer = null;
    let inputField = null;
    let sendButton = null;
    let typingIndicator = null;

    /**
     * Initialize the chat widget
     */
    function init() {
        createWidgetHTML();
        bindEvents();
        checkExistingConversation();
    }

    /**
     * Create the widget HTML structure
     */
    function createWidgetHTML() {
        const widgetHTML = `
            <div class="chat-widget" id="chat-widget">
                <!-- Floating Button -->
                <button class="chat-widget-button" id="chat-toggle-btn" aria-label="Open chat support">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    </svg>
                </button>

                <!-- Chat Window -->
                <div class="chat-window" id="chat-window">
                    <!-- Header -->
                    <div class="chat-header">
                        <div class="chat-header-title">
                            <div class="chat-avatar">AI</div>
                            <div>
                                <h3>Chat Support</h3>
                                <span>We typically respond instantly</span>
                            </div>
                        </div>
                        <div class="chat-header-actions">
                            <button id="chat-minimize-btn" aria-label="Minimize chat">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 13H5v-2h14v2z"/>
                                </svg>
                            </button>
                            <button id="chat-close-btn" aria-label="Close chat">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Escalated Banner -->
                    <div class="chat-escalated-banner" id="chat-escalated-banner">
                        Connected to human support - a team member will respond shortly
                    </div>

                    <!-- Error Banner -->
                    <div class="chat-error" id="chat-error"></div>

                    <!-- Messages Area -->
                    <div class="chat-messages" id="chat-messages">
                        <!-- Welcome state or messages will go here -->
                        <div class="chat-welcome" id="chat-welcome">
                            <div class="chat-welcome-icon">AI</div>
                            <h4>Hi there!</h4>
                            <p>I'm your AI assistant. I can help answer questions about your credit restoration case or the FCRA dispute process.</p>
                            <button class="chat-start-button" id="chat-start-btn">Start Chat</button>
                        </div>
                    </div>

                    <!-- Typing Indicator -->
                    <div class="chat-message assistant" style="margin: 0 16px 8px;">
                        <div class="typing-indicator" id="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>

                    <!-- Input Area -->
                    <div class="chat-input-area">
                        <form class="chat-input-form" id="chat-form">
                            <div class="chat-input-wrapper">
                                <textarea
                                    class="chat-input"
                                    id="chat-input"
                                    placeholder="Type your message..."
                                    rows="1"
                                    disabled
                                ></textarea>
                            </div>
                            <button type="submit" class="chat-send-button" id="chat-send-btn" disabled aria-label="Send message">
                                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                </svg>
                            </button>
                        </form>
                        <button class="chat-escalate-button" id="chat-escalate-btn" style="display: none;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                            Talk to a person
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Insert into DOM
        document.body.insertAdjacentHTML('beforeend', widgetHTML);

        // Cache DOM references
        widget = document.getElementById('chat-widget');
        chatWindow = document.getElementById('chat-window');
        messagesContainer = document.getElementById('chat-messages');
        inputField = document.getElementById('chat-input');
        sendButton = document.getElementById('chat-send-btn');
        typingIndicator = document.getElementById('typing-indicator');
    }

    /**
     * Bind event listeners
     */
    function bindEvents() {
        // Toggle button
        document.getElementById('chat-toggle-btn').addEventListener('click', toggleChat);

        // Close/minimize buttons
        document.getElementById('chat-minimize-btn').addEventListener('click', toggleChat);
        document.getElementById('chat-close-btn').addEventListener('click', closeChat);

        // Start chat button
        document.getElementById('chat-start-btn').addEventListener('click', startConversation);

        // Form submit
        document.getElementById('chat-form').addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });

        // Input field - auto-resize and enter to send
        inputField.addEventListener('input', autoResizeInput);
        inputField.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Escalate button
        document.getElementById('chat-escalate-btn').addEventListener('click', escalateChat);
    }

    /**
     * Toggle chat window open/closed
     */
    function toggleChat() {
        isOpen = !isOpen;
        chatWindow.classList.toggle('open', isOpen);

        if (isOpen && conversationId) {
            loadConversation();
            inputField.focus();
        }
    }

    /**
     * Close chat completely
     */
    function closeChat() {
        isOpen = false;
        chatWindow.classList.remove('open');
    }

    /**
     * Check for existing active conversation
     */
    function checkExistingConversation() {
        fetch('/portal/api/chat/conversations')
            .then(r => r.json())
            .then(data => {
                if (data.success && data.conversations && data.conversations.length > 0) {
                    const activeConv = data.conversations.find(c => c.status === 'active' || c.status === 'escalated');
                    if (activeConv) {
                        conversationId = activeConv.id;
                        isEscalated = activeConv.status === 'escalated';
                        enableChat();
                    }
                }
            })
            .catch(err => console.log('No existing conversation'));
    }

    /**
     * Start a new conversation
     */
    function startConversation() {
        if (isLoading) return;

        isLoading = true;
        document.getElementById('chat-start-btn').textContent = 'Starting...';

        fetch('/portal/api/chat/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    conversationId = data.conversation_id;
                    enableChat();

                    // Show welcome message
                    addMessage('assistant', data.welcome_message);
                } else {
                    showError(data.error || 'Failed to start chat');
                }
            })
            .catch(err => {
                showError('Connection error. Please try again.');
            })
            .finally(() => {
                isLoading = false;
                document.getElementById('chat-start-btn').textContent = 'Start Chat';
            });
    }

    /**
     * Enable chat input after conversation starts
     */
    function enableChat() {
        document.getElementById('chat-welcome').style.display = 'none';
        inputField.disabled = false;
        sendButton.disabled = false;
        document.getElementById('chat-escalate-btn').style.display = isEscalated ? 'none' : 'flex';

        if (isEscalated) {
            document.getElementById('chat-escalated-banner').classList.add('visible');
        }

        if (conversationId) {
            loadConversation();
        }
    }

    /**
     * Load conversation messages
     */
    function loadConversation() {
        if (!conversationId) return;

        fetch(`/portal/api/chat/conversation/${conversationId}`)
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    isEscalated = data.conversation.is_escalated;

                    // Clear and rebuild messages
                    const welcome = document.getElementById('chat-welcome');
                    messagesContainer.innerHTML = '';
                    messagesContainer.appendChild(welcome);
                    welcome.style.display = 'none';

                    data.messages.forEach(msg => {
                        addMessage(msg.role, msg.content, msg.created_at, msg.is_staff);
                    });

                    scrollToBottom();

                    // Update escalation UI
                    if (isEscalated) {
                        document.getElementById('chat-escalated-banner').classList.add('visible');
                        document.getElementById('chat-escalate-btn').style.display = 'none';
                    }
                }
            })
            .catch(err => console.error('Failed to load conversation:', err));
    }

    /**
     * Send a message
     */
    function sendMessage() {
        const message = inputField.value.trim();
        if (!message || isLoading || !conversationId) return;

        isLoading = true;
        sendButton.disabled = true;

        // Add user message immediately
        addMessage('user', message);
        inputField.value = '';
        autoResizeInput();

        // Show typing indicator
        showTyping(true);

        fetch('/portal/api/chat/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: conversationId,
                message: message
            })
        })
            .then(r => r.json())
            .then(data => {
                showTyping(false);

                if (data.success) {
                    addMessage('assistant', data.response);

                    // Check for escalation suggestion
                    if (data.escalation_suggested) {
                        showEscalationPrompt();
                    }
                } else {
                    showError(data.error || 'Failed to send message');
                }
            })
            .catch(err => {
                showTyping(false);
                showError('Connection error. Please try again.');
            })
            .finally(() => {
                isLoading = false;
                sendButton.disabled = false;
                inputField.focus();
            });
    }

    /**
     * Escalate chat to human support
     */
    function escalateChat() {
        if (isLoading || !conversationId) return;

        isLoading = true;
        document.getElementById('chat-escalate-btn').textContent = 'Connecting...';

        fetch('/portal/api/chat/escalate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: conversationId,
                reason: 'Client requested human support'
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    isEscalated = true;
                    document.getElementById('chat-escalated-banner').classList.add('visible');
                    document.getElementById('chat-escalate-btn').style.display = 'none';

                    addMessage('system', 'Connected to human support. A team member will respond shortly.');
                } else {
                    showError(data.error || 'Failed to connect to support');
                }
            })
            .catch(err => {
                showError('Connection error. Please try again.');
            })
            .finally(() => {
                isLoading = false;
                document.getElementById('chat-escalate-btn').innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                    Talk to a person
                `;
            });
    }

    /**
     * Add a message to the chat
     */
    function addMessage(role, content, timestamp, isStaff) {
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${role}`;

        const time = timestamp ? new Date(timestamp).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        }) : new Date().toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        });

        let staffLabel = '';
        if (isStaff && role === 'assistant') {
            staffLabel = '<div style="font-size: 11px; font-weight: 600; opacity: 0.7; margin-bottom: 4px;">Brightpath Team</div>';
        }

        messageEl.innerHTML = `
            <div class="message-content">
                ${staffLabel}
                ${escapeHtml(content)}
                <div class="message-time">${time}</div>
            </div>
        `;

        // Insert before typing indicator
        const typingParent = typingIndicator.parentElement;
        messagesContainer.insertBefore(messageEl, typingParent);

        scrollToBottom();
    }

    /**
     * Show/hide typing indicator
     */
    function showTyping(show) {
        typingIndicator.classList.toggle('visible', show);
        if (show) scrollToBottom();
    }

    /**
     * Show escalation prompt after AI suggests it
     */
    function showEscalationPrompt() {
        // The AI response already includes the escalation offer
        // Just make sure the button is visible
        if (!isEscalated) {
            document.getElementById('chat-escalate-btn').style.display = 'flex';
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        const errorEl = document.getElementById('chat-error');
        errorEl.textContent = message;
        errorEl.classList.add('visible');

        setTimeout(() => {
            errorEl.classList.remove('visible');
        }, 5000);
    }

    /**
     * Auto-resize textarea
     */
    function autoResizeInput() {
        inputField.style.height = 'auto';
        inputField.style.height = Math.min(inputField.scrollHeight, 100) + 'px';
    }

    /**
     * Scroll messages to bottom
     */
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
