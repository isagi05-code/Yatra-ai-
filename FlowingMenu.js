class FlowingMenu {
    constructor(container, items, options = {}) {
        this.container = container;
        this.items = items || [];
        this.speed = options.speed || 15;
        this.textColor = options.textColor || '#fff';
        this.bgColor = options.bgColor || '#120F17';
        this.marqueeBgColor = options.marqueeBgColor || '#fff';
        this.marqueeTextColor = options.marqueeTextColor || '#120F17';
        this.borderColor = options.borderColor || '#fff';

        if (this.container) {
            this.init();
        }
    }

    init() {
        this.container.innerHTML = '';
        const menuWrap = document.createElement('div');
        menuWrap.className = 'menu-wrap';
        menuWrap.style.backgroundColor = this.bgColor;

        const nav = document.createElement('nav');
        nav.className = 'menu';

        this.items.forEach(item => {
            const menuItem = this.createMenuItem(item);
            nav.appendChild(menuItem);
        });

        menuWrap.appendChild(nav);
        this.container.appendChild(menuWrap);
    }

    createMenuItem(item) {
        const menuItemWrap = document.createElement('div');
        menuItemWrap.className = 'menu__item';
        menuItemWrap.style.borderColor = this.borderColor;

        const link = document.createElement('a');
        link.className = 'menu__item-link';
        link.href = item.link || '#';
        link.textContent = item.text || '';
        link.style.color = this.textColor;

        const marquee = document.createElement('div');
        marquee.className = 'marquee';
        marquee.style.backgroundColor = this.marqueeBgColor;

        const marqueeInnerWrap = document.createElement('div');
        marqueeInnerWrap.className = 'marquee__inner-wrap';

        const marqueeInner = document.createElement('div');
        marqueeInner.className = 'marquee__inner';
        marqueeInner.setAttribute('aria-hidden', 'true');

        marqueeInnerWrap.appendChild(marqueeInner);
        marquee.appendChild(marqueeInnerWrap);
        menuItemWrap.appendChild(link);
        menuItemWrap.appendChild(marquee);

        let animation = null;

        const renderMarqueeParts = () => {
            marqueeInner.innerHTML = '';
            
            const part = document.createElement('div');
            part.className = 'marquee__part';
            part.style.color = this.marqueeTextColor;
            
            const span = document.createElement('span');
            span.textContent = item.text || '';
            
            const img = document.createElement('div');
            img.className = 'marquee__img';
            img.style.backgroundImage = `url(${item.image || ''})`;
            
            part.appendChild(span);
            part.appendChild(img);
            marqueeInner.appendChild(part);

            const contentWidth = part.offsetWidth;
            if (contentWidth === 0) {
                // Not rendered yet, try again
                setTimeout(renderMarqueeParts, 50);
                return;
            }

            const viewportWidth = window.innerWidth;
            const needed = Math.max(4, Math.ceil(viewportWidth / contentWidth) + 2);

            for (let i = 1; i < needed; i++) {
                const clone = part.cloneNode(true);
                marqueeInner.appendChild(clone);
            }

            if (animation) animation.kill();
            animation = gsap.to(marqueeInner, {
                x: -contentWidth,
                duration: this.speed,
                ease: 'none',
                repeat: -1
            });
        };

        setTimeout(renderMarqueeParts, 50);
        window.addEventListener('resize', renderMarqueeParts);

        const animationDefaults = { duration: 0.6, ease: 'expo' };

        const findClosestEdge = (x, y, width, height) => {
            const topEdgeDist = distMetric(x, y, width / 2, 0);
            const bottomEdgeDist = distMetric(x, y, width / 2, height);
            return topEdgeDist < bottomEdgeDist ? 'top' : 'bottom';
        };

        const distMetric = (x, y, x2, y2) => {
            const xDiff = x - x2;
            const yDiff = y - y2;
            return xDiff * xDiff + yDiff * yDiff;
        };

        link.addEventListener('mouseenter', ev => {
            const rect = menuItemWrap.getBoundingClientRect();
            const x = ev.clientX - rect.left;
            const y = ev.clientY - rect.top;
            const edge = findClosestEdge(x, y, rect.width, rect.height);

            gsap.timeline({ defaults: animationDefaults })
                .set(marquee, { y: edge === 'top' ? '-101%' : '101%' }, 0)
                .set(marqueeInner, { y: edge === 'top' ? '101%' : '-101%' }, 0)
                .to([marquee, marqueeInner], { y: '0%' }, 0);
        });

        link.addEventListener('mouseleave', ev => {
            const rect = menuItemWrap.getBoundingClientRect();
            const x = ev.clientX - rect.left;
            const y = ev.clientY - rect.top;
            const edge = findClosestEdge(x, y, rect.width, rect.height);

            gsap.timeline({ defaults: animationDefaults })
                .to(marquee, { y: edge === 'top' ? '-101%' : '101%' }, 0)
                .to(marqueeInner, { y: edge === 'top' ? '101%' : '-101%' }, 0);
        });

        return menuItemWrap;
    }
}
