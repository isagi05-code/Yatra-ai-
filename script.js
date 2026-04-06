document.addEventListener('DOMContentLoaded', () => {
    // Data for the destinations
    const destinations = [
        {
            title1: "TAJ",
            title2: "MAHAL",
            subtitle: "Agra - Uttar Pradesh",
            description: "An immense mausoleum of white marble, built in Agra by Mughal emperor Shah Jahan. It is one of the universally admired masterpieces of the world's heritage and a symbol of India's rich history.",
            bgId: "bg-0"
        },
        {
            title1: "ROHTANG",
            title2: "PASS",
            subtitle: "Manali - Himachal Pradesh",
            description: "A high mountain pass on the eastern end of the Pir Panjal Range of the Himalayas. Manali is a magnetic high-altitude Himalayan resort town known for its breathtaking snow-capped peaks and adventure sports.",
            bgId: "bg-1"
        },
        {
            title1: "PALOLEM",
            title2: "BEACH",
            subtitle: "Goa - India",
            description: "Known for its beautiful crescent shape, Palolem Beach in South Goa is fringed by a thick forest of coconut palms. It's the perfect destination for relaxation, vibrant nightlife, and stunning Arabian Sea sunsets.",
            bgId: "bg-2"
        },
        {
            title1: "HAWA",
            title2: "MAHAL",
            subtitle: "Jaipur - Rajasthan",
            description: "The 'Palace of Winds' is a stunning pink sandstone palace in Jaipur. Its unique five-story exterior is akin to a honeycomb, originally built so royal women could observe everyday life and festivals in the street below.",
            bgId: "bg-3"
        },
        {
            title1: "MUNNAR",
            title2: "VALLEY",
            subtitle: "Kerala - India",
            description: "Munnar is a town in the Western Ghats mountain range in India’s Kerala state. It's surrounded by rolling hills dotted with tea plantations established in the late 19th century, offering a tranquil and lush green escape.",
            bgId: "bg-4"
        }
    ];

    let currentIndex = 0;
    const totalSlides = destinations.length;
    let autoPlayInterval;

    // DOM Elements
    const heroTitle1 = document.getElementById('hero-title1');
    const heroTitle2 = document.getElementById('hero-title2');
    const heroSubtitle = document.getElementById('hero-subtitle');
    const heroDesc = document.getElementById('hero-desc');
    const bgLayers = document.querySelectorAll('.bg-layer');
    const cards = document.querySelectorAll('.card');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const slideNumber = document.getElementById('slideNumber');
    const progressFill = document.getElementById('progressFill');
    
    // Audio Elements
    const btnPlay = document.querySelector('.btn-play');
    const btnPlayIcon = btnPlay.querySelector('i');
    const bgMusic = document.getElementById('bgMusic');
    
    // Set initial play icon state
    btnPlayIcon.classList.remove('fa-pause');
    btnPlayIcon.classList.add('fa-play');

    // Function to change the active slide
    function goToSlide(index) {
        // Handle wrapping
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;

        currentIndex = index;
        const data = destinations[currentIndex];

        // 1. Update Hero Text with a slight fade animation
        const heroContent = document.querySelector('.hero-content');
        heroContent.style.opacity = '0';
        heroContent.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            heroTitle1.textContent = data.title1;
            heroTitle2.textContent = data.title2;
            heroSubtitle.textContent = data.subtitle;
            heroDesc.textContent = data.description;
            
            heroContent.style.transition = 'opacity 0.6s, transform 0.6s';
            heroContent.style.opacity = '1';
            heroContent.style.transform = 'translateY(0)';
        }, 300);

        // 2. Update Background Layers (Crossfade)
        bgLayers.forEach(layer => layer.classList.remove('active'));
        document.getElementById(data.bgId).classList.add('active');

        // 3. Update Cards UI
        cards.forEach((card, idx) => {
            // Reset state
            card.classList.remove('active');
            card.style.display = 'block';
            
            // Highlight active, but typically in the UI, the active card is "hidden" from the right list 
            // since it's the main background, but let's keep it visible with an active border for better UX, 
            // or we can mirror the design where the active isn't in the carousel. 
            // The sample shows 4 cards for 5 items. The active one is the background.
            
            if(idx === currentIndex) {
                card.style.display = 'none'; // Hide the active destination from the carousel cards
            } else {
                card.style.display = 'block'; // Show others
            }
        });

        // 4. Update numbering and progress bar
        slideNumber.textContent = `0${currentIndex + 1}`;
        const progressPercentage = ((currentIndex + 1) / totalSlides) * 100;
        progressFill.style.width = `${progressPercentage}%`;

        // 5. Reset AutoPlay when manually triggered
        resetAutoPlay();
    }

    // Event Listeners for Nav Arrows
    prevBtn.addEventListener('click', () => goToSlide(currentIndex - 1));
    nextBtn.addEventListener('click', () => goToSlide(currentIndex + 1));

    // Event Listeners for Cards
    cards.forEach((card) => {
        card.addEventListener('click', function() {
            const index = parseInt(this.getAttribute('data-index'));
            goToSlide(index);
        });
    });

    // Event Listener for Play Button
    btnPlay.addEventListener('click', () => {
        if (bgMusic.paused) {
            bgMusic.play();
            btnPlayIcon.classList.remove('fa-play');
            btnPlayIcon.classList.add('fa-pause');
        } else {
            bgMusic.pause();
            btnPlayIcon.classList.remove('fa-pause');
            btnPlayIcon.classList.add('fa-play');
        }
    });

    // Auto Play Functionality
    function startAutoPlay() {
        autoPlayInterval = setInterval(() => {
            goToSlide(currentIndex + 1);
        }, 8000); // Change slide every 8 seconds
    }

    function resetAutoPlay() {
        clearInterval(autoPlayInterval);
        startAutoPlay();
    }

    // Initialize first slide
    goToSlide(0); 
    startAutoPlay();

    // Intersection Observer for Holiday Cards Animation
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const cardObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add a slight stagger effect based on the card's index in the grid
                const cardIndex = Array.from(document.querySelectorAll('.holiday-card')).indexOf(entry.target);
                const delay = (cardIndex % 4) * 100; // stagger 0, 100, 200, 300 ms for rows
                
                setTimeout(() => {
                    entry.target.classList.add('show');
                }, delay);
                
                observer.unobserve(entry.target); // Stop observing once shown
            }
        });
    }, observerOptions);

    // Observe all holiday cards
    document.querySelectorAll('.holiday-card').forEach(card => {
        cardObserver.observe(card);
    });
});
