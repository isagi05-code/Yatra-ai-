document.addEventListener('DOMContentLoaded', () => {

    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // Store conversation context if we are resuming
    let chatbotContextInfo = "";

    // Helper to scroll to bottom smoothly
    const scrollToBottom = () => {
        setTimeout(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        }, 50);
    };

    // Helper to append a message
    const appendMessage = (text, sender, isMarkdown = false) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        let avatarHTML = '';
        if (sender === 'bot') {
            avatarHTML = `<div class="msg-avatar" style="border: 2px solid #f7a02c;"><img src="yatralogo.jpg" alt="Agent" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>`;
        } else {
            avatarHTML = `<div class="msg-avatar user-avatar"><i class="fa-solid fa-user"></i></div>`;
        }

        const contentHTML = `
            <div class="msg-content">
                ${isMarkdown ? marked.parse(text) : `<p>${text}</p>`}
            </div>
        `;

        msgDiv.innerHTML = avatarHTML + contentHTML;

        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    };

    // AI Logic Simulator connecting to companion_app.py
    const getBotResponse = async (userInput) => {
        try {
            let userId = null;
            const userStr = localStorage.getItem('yatraUser');
            if (userStr) {
                try {
                    const user = JSON.parse(userStr);
                    userId = user.id;
                } catch(e) {}
            }

            const response = await fetch('/api/companion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: userInput,
                    context: chatbotContextInfo,
                    user_id: userId
                })
            });
            const data = await response.json();
            return data.reply;
        } catch (error) {
            console.error("AI Network Error:", error);
            return "I'm having trouble connecting to the network right now. Please make sure the companion backend is running.";
        }
    };

    // Handle sending message
    const handleSend = async () => {
        const text = chatInput.value.trim();
        if (!text) return;

        // Hide empty state if present
        const emptyStateGreeting = document.getElementById('emptyStateGreeting');
        if (emptyStateGreeting) emptyStateGreeting.style.display = 'none';

        // Append user
        appendMessage(text, 'user', false);
        chatInput.value = '';

        // Typing indicator
        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = typingId;
        typingDiv.innerHTML = `
            <div class="msg-avatar" style="border: 2px solid #f7a02c;"><img src="yatralogo.jpg" alt="Agent" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>
            <div class="msg-content"><p>...</p></div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();

        // Get Bot Response
        const responseText = await getBotResponse(text);

        // Remove typing and append bot response parsed as Markdown
        document.getElementById(typingId).remove();
        appendMessage(responseText, 'bot', true);
    };

    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    // Handle Chat Resumption
    const resumeChatIfNeeded = async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const resumeId = urlParams.get('resume_id');
        
        if (resumeId) {
            try {
                // Fetch the historic log from the main server
                const response = await fetch(`/api/logs/${resumeId}`);
                if (response.ok) {
                    const data = await response.json();
                    
                    // Hide empty state
                    const emptyStateGreeting = document.getElementById('emptyStateGreeting');
                    if (emptyStateGreeting) emptyStateGreeting.style.display = 'none';
                    
                    // If the historical response was an Itinerary JSON, parse it to look pretty in the chat bubble
                    let botReplyToShow = data.bot_response;
                    try {
                        const parsed = JSON.parse(data.bot_response);
                        if (parsed && parsed.reply) botReplyToShow = parsed.reply;
                    } catch (e) {}
                    
                    // Render the historical chat 
                    appendMessage(data.user_message, 'user', false);
                    appendMessage(botReplyToShow, 'bot', true);
                    
                    // Save the FULL raw data into memory for subsequent messages so it remembers the itinerary
                    chatbotContextInfo = `User: ${data.user_message}\nBot: ${data.bot_response}`;
                }
            } catch (err) {
                console.error("Failed to load historical log:", err);
            }
        }
    };

    resumeChatIfNeeded();
});
