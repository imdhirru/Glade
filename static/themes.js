// Theme configurations
const themes = {
    ocean: {
        name: 'Ocean',
        primary: '#667eea',
        accent: '#764ba2',
        bgColor: '#f0f4f8'
    },
    sunset: {
        name: 'Sunset',
        primary: '#f093fb',
        accent: '#f5576c',
        bgColor: '#fff5f7'
    },
    forest: {
        name: 'Forest',
        primary: '#0ba360',
        accent: '#3cba92',
        bgColor: '#f0f8f5'
    },
    gold: {
        name: 'Gold',
        primary: '#d4a574',
        accent: '#1a1a2e',
        bgColor: '#faf7f2'
    },
    night: {
        name: 'Night',
        primary: '#c05c7e',
        accent: '#2d3561',
        bgColor: '#1a1a2e'
    },
    cyber: {
        name: 'Cyber',
        primary: '#00fff0',
        accent: '#0080ff',
        bgColor: '#0a0e27'
    }
};

function getThemeConfig(themeName) {
    return themes[themeName] || themes.ocean;
}

function applyThemeColors(themeName) {
    const theme = getThemeConfig(themeName);
    document.documentElement.style.setProperty('--primary', theme.primary);
    document.documentElement.style.setProperty('--accent', theme.accent);
    document.documentElement.style.setProperty('--bg-color', theme.bgColor);
}