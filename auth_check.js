document.addEventListener('DOMContentLoaded', () => {
    const userStr = localStorage.getItem('yatraUser');
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            const userLink = document.querySelector('.nav-icons a[href="/signin.html"], .nav-icons a[href="signin.html"]');
            
            if (userLink) {
                // Change the link to not redirect
                userLink.href = '#';
                
                // Keep the button styling but modify the content
                const btn = userLink.querySelector('button');
                if (btn) {
                    btn.classList.add('user-logged-in');
                    btn.style.width = 'auto';
                    btn.style.padding = '4px 12px 4px 4px';
                    btn.style.display = 'flex';
                    btn.style.alignItems = 'center';
                    btn.style.gap = '8px';
                    btn.style.borderRadius = '50px';
                    
                    const firstName = user.name ? user.name.split(' ')[0] : 'User';
                    const pic = user.picture || 'yatralogo.jpg';
                    
                    btn.innerHTML = `
                        <img src="${pic}" alt="${firstName}" style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 0.85rem; font-weight: 600;">${firstName}</span>
                    `;
                    
                    // Create dropdown for logout
                    let dropdown = document.getElementById('user-dropdown');
                    if (!dropdown) {
                        dropdown = document.createElement('div');
                        dropdown.id = 'user-dropdown';
                        dropdown.style.display = 'none';
                        dropdown.style.position = 'absolute';
                        dropdown.style.top = '100%';
                        dropdown.style.right = '0';
                        dropdown.style.marginTop = '10px';
                        dropdown.style.background = 'rgba(0,0,0,0.9)';
                        dropdown.style.border = '1px solid var(--primary-color, #f7a02c)';
                        dropdown.style.padding = '8px';
                        dropdown.style.borderRadius = '8px';
                        dropdown.style.zIndex = '1000';
                        dropdown.style.minWidth = '120px';
                        dropdown.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
                        
                        const logoutBtn = document.createElement('button');
                        logoutBtn.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket" style="margin-right:8px;"></i> Logout';
                        logoutBtn.style.width = '100%';
                        logoutBtn.style.padding = '10px';
                        logoutBtn.style.background = 'transparent';
                        logoutBtn.style.color = '#fff';
                        logoutBtn.style.border = 'none';
                        logoutBtn.style.cursor = 'pointer';
                        logoutBtn.style.fontFamily = "'Inter', sans-serif";
                        logoutBtn.style.textAlign = 'left';
                        logoutBtn.style.borderRadius = '4px';
                        logoutBtn.style.fontSize = '0.9rem';
                        
                        logoutBtn.onmouseover = () => logoutBtn.style.background = 'rgba(255,255,255,0.1)';
                        logoutBtn.onmouseout = () => logoutBtn.style.background = 'transparent';
                        
                        logoutBtn.onclick = (e) => {
                            e.preventDefault();
                            localStorage.removeItem('yatraUser');
                            window.location.reload();
                        };
                        
                        dropdown.appendChild(logoutBtn);
                        userLink.parentElement.style.position = 'relative';
                        userLink.parentElement.appendChild(dropdown);
                    }
                    
                    userLink.onclick = (e) => {
                        e.preventDefault();
                        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
                    };
                    
                    // Close dropdown if clicking outside
                    document.addEventListener('click', (e) => {
                        if (!userLink.parentElement.contains(e.target)) {
                            dropdown.style.display = 'none';
                        }
                    });
                }
            }
        } catch (error) {
            console.error("Error parsing user data from localStorage", error);
        }
    }
});
