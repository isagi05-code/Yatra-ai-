document.addEventListener('DOMContentLoaded', () => {

    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');

    // Store conversation for context
    let requestedPdfGuide = null;
    let dynamicItinerary = null;
    let dynamicAirbnbs = [];
    let dynamicRestaurants = [];
    let dynamicCafes = [];

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
    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        let avatarHTML = '';
        if (sender === 'bot') {
            avatarHTML = `<div class="msg-avatar"><img src="yatralogo.jpg" alt="Agent" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>`;
        } else {
            avatarHTML = `<div class="msg-avatar user-avatar"><i class="fa-solid fa-user"></i></div>`;
        }

        const contentHTML = `
            <div class="msg-content">
                <p>${text}</p>
            </div>
        `;

        msgDiv.innerHTML = avatarHTML + contentHTML;

        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    };

    // AI Logic Simulator
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

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userInput, user_id: userId })
            });
            const data = await response.json();

            if (data.itinerary && data.itinerary.length > 0) {
                requestedPdfGuide = data.destination;
                dynamicItinerary = data.itinerary;
                dynamicAirbnbs = data.airbnb_links || [];
                dynamicRestaurants = data.restaurants || [];
                dynamicCafes = data.cafes || [];
                downloadPdfBtn.style.display = 'flex';
            }

            return data.reply;
        } catch (error) {
            console.error("AI Network Error:", error);
            return "I'm having trouble connecting to the intelligence network. Please try again later.";
        }
    };

    // Handle sending message
    const handleSend = async () => {
        const text = chatInput.value.trim();
        if (!text) return;

        // Hide empty state if present
        const emptyStateGreeting = document.getElementById('emptyStateGreeting');
        const suggestionChips = document.getElementById('suggestionChips');
        if (emptyStateGreeting) emptyStateGreeting.style.display = 'none';
        if (suggestionChips) suggestionChips.style.display = 'none';

        // Append user
        appendMessage(text, 'user');
        chatInput.value = '';

        // Typing indicator
        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = typingId;
        typingDiv.innerHTML = `
            <div class="msg-avatar"><img src="yatralogo.jpg" alt="Agent" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>
            <div class="msg-content"><p>...</p></div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();

        // Get Bot Response
        const responseText = await getBotResponse(text);

        // Remove typing and append bot response
        document.getElementById(typingId).remove();
        appendMessage(responseText, 'bot');
    };

    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    // Handle PDF Generation
    downloadPdfBtn.addEventListener('click', () => {
        if (!window.jspdf) {
            alert("PDF Generation Library not loaded. Please try again later.");
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        const dest = requestedPdfGuide || "Curated Multi-City";

        // Add Premium Styling to PDF
        // Header background - beautiful dark slate color
        doc.setFillColor(15, 23, 42); 
        doc.rect(0, 0, 210, 45, 'F');

        // Brand Name
        doc.setTextColor(247, 160, 44); // Primary orange
        doc.setFontSize(30);
        doc.setFont('helvetica', 'bold');
        doc.text("YATRA.AI", 20, 23);

        // Subtitle
        doc.setTextColor(200, 200, 200);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'italic');
        doc.text("PREMIUM ITINERARY DOSSIER", 20, 33);
        
        // Header separator line
        doc.setDrawColor(247, 160, 44);
        doc.setLineWidth(1);
        doc.line(20, 38, 190, 38);

        // Main Content Head
        doc.setTextColor(30, 30, 30);
        doc.setFontSize(24);
        doc.setFont('helvetica', 'bold');
        doc.text(`Destination: ${dest}`, 20, 60);

        let currentY = 75;
        const lineSpacing = 8;
        const pageHeight = 280;

        const checkPageBreak = (neededSpace) => {
            if (currentY + neededSpace > pageHeight) {
                doc.addPage();
                currentY = 20;
            }
        };

        // Custom content section header helper
        const renderSectionHeader = (title, colorHex) => {
            checkPageBreak(20);
            doc.setFillColor(colorHex[0], colorHex[1], colorHex[2]); 
            doc.rect(20, currentY, 170, 10, 'F');
            doc.setFontSize(14);
            doc.setTextColor(255, 255, 255);
            doc.setFont('helvetica', 'bold');
            doc.text(title, 22, currentY + 7);
            currentY += 18;
        }

        // Daily Itinerary
        if (dynamicItinerary && Array.isArray(dynamicItinerary) && dynamicItinerary.length > 0) {
            renderSectionHeader("Daily Itinerary", [44, 62, 80]); // Navy blueish banner
            
            doc.setFontSize(11);
            doc.setTextColor(50, 50, 50);

            dynamicItinerary.forEach(dayInfo => {
                checkPageBreak(25);
                doc.setFont('helvetica', 'bold');
                doc.text(`Day ${dayInfo.day}:`, 20, currentY);
                doc.setFont('helvetica', 'normal');
                const textLines = doc.splitTextToSize(`${dayInfo.activity}`, 155);
                doc.text(textLines, 35, currentY);
                currentY += (lineSpacing * textLines.length) + 4;
            });
            currentY += 5;
        }

        // Airbnb Links
        if (dynamicAirbnbs && Array.isArray(dynamicAirbnbs) && dynamicAirbnbs.length > 0) {
            renderSectionHeader("Top Airbnb Stays", [217, 119, 6]); // Amber banner

            doc.setFontSize(11);
            doc.setTextColor(0, 102, 204); // subtle link color
            doc.setFont('helvetica', 'normal');

            dynamicAirbnbs.forEach(link => {
                checkPageBreak(12);
                const textLines = doc.splitTextToSize(`• ${link}`, 165);
                doc.text(textLines, 20, currentY);
                currentY += (lineSpacing * textLines.length);
            });
            currentY += 5;
        }

        // Restaurants
        if (dynamicRestaurants && Array.isArray(dynamicRestaurants) && dynamicRestaurants.length > 0) {
            renderSectionHeader("Culinary Highlights & Restaurants", [225, 29, 72]); // Rose/Red banner

            doc.setFontSize(11);
            doc.setTextColor(60, 60, 60);
            doc.setFont('helvetica', 'italic');

            dynamicRestaurants.forEach(restaurant => {
                checkPageBreak(12);
                const textLines = doc.splitTextToSize(`• ${restaurant}`, 165);
                doc.text(textLines, 20, currentY);
                currentY += (lineSpacing * textLines.length);
            });
            currentY += 5;
        }

        // Cafes
        if (dynamicCafes && Array.isArray(dynamicCafes) && dynamicCafes.length > 0) {
            renderSectionHeader("Cozy Cafes Nearby", [109, 40, 217]); // Purple banner

            doc.setFontSize(11);
            doc.setTextColor(60, 60, 60);
            doc.setFont('helvetica', 'italic');

            dynamicCafes.forEach(cafe => {
                checkPageBreak(12);
                const textLines = doc.splitTextToSize(`• ${cafe}`, 165);
                doc.text(textLines, 20, currentY);
                currentY += (lineSpacing * textLines.length);
            });
            currentY += 5;
        }

        checkPageBreak(40);
        currentY += 15;
        doc.setDrawColor(200, 200, 200);
        doc.setLineWidth(0.5);
        doc.line(20, currentY, 190, currentY);
        currentY += 10;

        doc.setTextColor(150, 150, 150);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text("Redefining global mobility for the modern visionary.", 20, currentY);

        // Download Document
        doc.save(`Yatra_Itinerary_${dest.replace(/\s+/g, '_')}.pdf`);

        // Hide button after download and send confirmation
        downloadPdfBtn.style.display = 'none';
        appendMessage(`Your PDF Guide for ${dest} has been generated and downloaded. Is there anything else I can assist you with today?`, 'bot');
    });

});
