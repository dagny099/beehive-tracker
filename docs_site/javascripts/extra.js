/* Custom JavaScript for Beehive Tracker documentation */

document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe all cards for animation
    document.querySelectorAll('.card, .feature-card').forEach(card => {
        observer.observe(card);
    });

    // Enhanced code block copy functionality
    document.querySelectorAll('.highlight').forEach(block => {
        const button = document.createElement('button');
        button.innerHTML = '📋 Copy';
        button.className = 'copy-button';
        button.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: var(--md-accent-fg-color);
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        block.style.position = 'relative';
        block.appendChild(button);
        
        block.addEventListener('mouseenter', () => button.style.opacity = '1');
        block.addEventListener('mouseleave', () => button.style.opacity = '0');
        
        button.addEventListener('click', () => {
            const code = block.querySelector('code');
            if (code) {
                navigator.clipboard.writeText(code.textContent).then(() => {
                    button.innerHTML = '✅ Copied!';
                    setTimeout(() => button.innerHTML = '📋 Copy', 2000);
                });
            }
        });
    });

    // Add progress indicators to installation steps
    const installSteps = document.querySelectorAll('.installation-step');
    installSteps.forEach((step, index) => {
        const progress = document.createElement('div');
        progress.className = 'step-progress';
        progress.innerHTML = `Step ${index + 1} of ${installSteps.length}`;
        progress.style.cssText = `
            background: var(--bee-yellow);
            color: var(--hive-brown);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 8px;
        `;
        step.insertBefore(progress, step.firstChild);
    });

    // Add interactive tooltips for technical terms
    const techTerms = {
        'EXIF': 'Exchangeable Image File Format - metadata embedded in photos',
        'API': 'Application Programming Interface - how different software components communicate',
        'JSON': 'JavaScript Object Notation - a lightweight data interchange format',
        'CSV': 'Comma-Separated Values - a simple format for tabular data'
    };

    Object.keys(techTerms).forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    return node.parentNode.tagName !== 'CODE' && 
                           node.parentNode.tagName !== 'PRE' ? 
                           NodeFilter.FILTER_ACCEPT : 
                           NodeFilter.FILTER_REJECT;
                }
            }
        );

        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (regex.test(node.textContent)) {
                textNodes.push(node);
            }
        }

        textNodes.forEach(textNode => {
            const html = textNode.textContent.replace(regex, match => 
                `<span class="tech-term" data-tooltip="${techTerms[term.toUpperCase()]}">${match}</span>`
            );
            const wrapper = document.createElement('span');
            wrapper.innerHTML = html;
            textNode.parentNode.replaceChild(wrapper, textNode);
        });
    });

    // Style tech term tooltips
    const style = document.createElement('style');
    style.textContent = `
        .tech-term {
            border-bottom: 1px dotted var(--md-accent-fg-color);
            cursor: help;
            position: relative;
        }
        
        .tech-term::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--md-default-bg-color);
            color: var(--md-default-fg-color);
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            white-space: nowrap;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            z-index: 1000;
        }
        
        .tech-term:hover::after {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    // Add "Back to top" button
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '↑ Top';
    backToTop.className = 'back-to-top';
    backToTop.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--md-primary-fg-color);
        color: white;
        border: none;
        padding: 12px 16px;
        border-radius: 25px;
        cursor: pointer;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 1000;
    `;

    document.body.appendChild(backToTop);

    // Show/hide back to top button
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.style.opacity = '1';
            backToTop.style.transform = 'translateY(0)';
        } else {
            backToTop.style.opacity = '0';
            backToTop.style.transform = 'translateY(10px)';
        }
    });

    backToTop.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Add keyboard navigation hints
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search (if available)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            const searchButton = document.querySelector('[data-md-component="search-button"]');
            if (searchButton) {
                e.preventDefault();
                searchButton.click();
            }
        }
    });

    // Initialize any chart animations if present
    const charts = document.querySelectorAll('.mermaid');
    charts.forEach(chart => {
        chart.style.opacity = '0';
        chart.style.transform = 'translateY(20px)';
        chart.style.transition = 'all 0.5s ease';
        
        observer.observe(chart);
        chart.addEventListener('transitionend', () => {
            chart.style.opacity = '1';
            chart.style.transform = 'translateY(0)';
        });
    });

    // Add loading state for external content
    const externalLinks = document.querySelectorAll('a[href^="http"]');
    externalLinks.forEach(link => {
        if (!link.hostname.includes(window.location.hostname)) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
            link.innerHTML += ' <span style="font-size: 0.8em;">↗</span>';
        }
    });

    console.log('🐝 Beehive Tracker documentation enhanced!');
});