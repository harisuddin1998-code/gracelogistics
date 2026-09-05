// Complete Theme Management System
class ThemeManager {
    constructor() {
        this.themes = {
            'windows11': {
                name: 'Windows 11 Light',
                icon: 'fa-solid fa-sun',
                colors: {
                    '--bg-primary': '#ffffff',
                    '--bg-secondary': '#f3f3f3',
                    '--text-primary': '#000000',
                    '--text-secondary': '#616161',
                    '--accent-color': '#0078d4',
                    '--accent-hover': '#106ebe',
                    '--border-color': '#e0e0e0',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#ffffff',
                    '--footer-bg': '#f3f3f3',
                    '--success': '#107c10',
                    '--danger': '#d13438',
                    '--warning': '#ffaa44',
                    '--info': '#0078d4'
                }
            },
            'windows11-dark': {
                name: 'Windows 11 Dark',
                icon: 'fa-solid fa-moon',
                colors: {
                    '--bg-primary': '#1c1c1c',
                    '--bg-secondary': '#2d2d2d',
                    '--text-primary': '#ffffff',
                    '--text-secondary': '#a0a0a0',
                    '--accent-color': '#0078d4',
                    '--accent-hover': '#106ebe',
                    '--border-color': '#404040',
                    '--card-bg': '#2d2d2d',
                    '--navbar-bg': '#1c1c1c',
                    '--footer-bg': '#1c1c1c',
                    '--success': '#107c10',
                    '--danger': '#d13438',
                    '--warning': '#ffaa44',
                    '--info': '#0078d4'
                }
            },
            'classic': {
                name: 'Windows Classic',
                icon: 'fa-solid fa-desktop',
                colors: {
                    '--bg-primary': '#3a6ea5',
                    '--bg-secondary': '#ece9d8',
                    '--text-primary': '#000000',
                    '--text-secondary': '#444444',
                    '--accent-color': '#316ac5',
                    '--accent-hover': '#2655a0',
                    '--border-color': '#aca899',
                    '--card-bg': '#ece9d8',
                    '--navbar-bg': '#3a6ea5',
                    '--footer-bg': '#3a6ea5',
                    '--success': '#107c10',
                    '--danger': '#d13438',
                    '--warning': '#ffaa44',
                    '--info': '#316ac5'
                }
            },
            'corporate': {
                name: 'Corporate Blue',
                icon: 'fa-solid fa-building',
                colors: {
                    '--bg-primary': '#ffffff',
                    '--bg-secondary': '#ecf0f1',
                    '--text-primary': '#2c3e50',
                    '--text-secondary': '#7f8c8d',
                    '--accent-color': '#2980b9',
                    '--accent-hover': '#1c638c',
                    '--border-color': '#bdc3c7',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#2c3e50',
                    '--footer-bg': '#2c3e50',
                    '--success': '#27ae60',
                    '--danger': '#e74c3c',
                    '--warning': '#f39c12',
                    '--info': '#2980b9'
                }
            },
            'nature': {
                name: 'Nature Green',
                icon: 'fa-solid fa-leaf',
                colors: {
                    '--bg-primary': '#f0f7e8',
                    '--bg-secondary': '#e8f5e9',
                    '--text-primary': '#1b5e20',
                    '--text-secondary': '#4caf50',
                    '--accent-color': '#2ecc71',
                    '--accent-hover': '#27ae60',
                    '--border-color': '#c8e6c9',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#1b5e20',
                    '--footer-bg': '#1b5e20',
                    '--success': '#2ecc71',
                    '--danger': '#e74c3c',
                    '--warning': '#f39c12',
                    '--info': '#3498db'
                }
            },
            'sunset': {
                name: 'Sunset Orange',
                icon: 'fa-solid fa-sun',
                colors: {
                    '--bg-primary': '#fff5e6',
                    '--bg-secondary': '#ffe0b2',
                    '--text-primary': '#e65100',
                    '--text-secondary': '#f57c00',
                    '--accent-color': '#e67e22',
                    '--accent-hover': '#d35400',
                    '--border-color': '#ffcc80',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#e65100',
                    '--footer-bg': '#e65100',
                    '--success': '#27ae60',
                    '--danger': '#e74c3c',
                    '--warning': '#f39c12',
                    '--info': '#3498db'
                }
            },
            'purple': {
                name: 'Royal Purple',
                icon: 'fa-solid fa-crown',
                colors: {
                    '--bg-primary': '#f3e5f5',
                    '--bg-secondary': '#e1bee7',
                    '--text-primary': '#4a148c',
                    '--text-secondary': '#9b59b6',
                    '--accent-color': '#9b59b6',
                    '--accent-hover': '#8e44ad',
                    '--border-color': '#ce93d8',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#4a148c',
                    '--footer-bg': '#4a148c',
                    '--success': '#27ae60',
                    '--danger': '#e74c3c',
                    '--warning': '#f39c12',
                    '--info': '#3498db'
                }
            },
            'ocean': {
                name: 'Ocean Teal',
                icon: 'fa-solid fa-water',
                colors: {
                    '--bg-primary': '#e0f2f1',
                    '--bg-secondary': '#b2dfdb',
                    '--text-primary': '#004d40',
                    '--text-secondary': '#00897b',
                    '--accent-color': '#16a085',
                    '--accent-hover': '#1abc9c',
                    '--border-color': '#80cbc4',
                    '--card-bg': '#ffffff',
                    '--navbar-bg': '#004d40',
                    '--footer-bg': '#004d40',
                    '--success': '#27ae60',
                    '--danger': '#e74c3c',
                    '--warning': '#f39c12',
                    '--info': '#3498db'
                }
            }
        };
        
        this.loadSavedTheme();
    }
    
    applyTheme(themeId) {
        const theme = this.themes[themeId];
        if (!theme) return;
        
        const root = document.documentElement;
        for (const [key, value] of Object.entries(theme.colors)) {
            root.style.setProperty(key, value);
        }
        
        localStorage.setItem('activeTheme', themeId);
        this.updateThemeIndicator(themeId);
    }
    
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('activeTheme');
        if (savedTheme && this.themes[savedTheme]) {
            this.applyTheme(savedTheme);
        } else {
            this.applyTheme('windows11');
        }
    }
    
    updateThemeIndicator(themeId) {
        const themeName = this.themes[themeId].name;
        const indicator = document.getElementById('current-theme-name');
        if (indicator) indicator.innerText = themeName;
        
        // Update active state in UI
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === themeId) {
                option.classList.add('active');
            }
        });
    }
    
    getThemeList() {
        return Object.entries(this.themes).map(([id, theme]) => ({
            id: id,
            name: theme.name,
            icon: theme.icon
        }));
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();