/**
 * 主题管理工具
 * 负责存储、应用和切换不同的UI主题
 */

// 可用主题列表
const THEMES = {
    default: {
        name: '默认主题',
        vars: {
            '--primary-color': '#3498db',
            '--primary-light': '#e3f2fd',
            '--primary-dark': '#1976d2',
            '--body-bg': '#f8f9fa',
            '--sidebar-bg': '#f8f9fa',
            '--content-bg': '#ffffff',
            '--text-primary': '#212529',
            '--text-secondary': '#6c757d',
            '--text-light': '#adb5bd',
            '--border-color': '#dee2e6'
        }
    },
    dark: {
        name: '深色模式',
        vars: {
            '--primary-color': '#3498db',
            '--primary-light': '#2f4f6f',
            '--primary-dark': '#1d6fa5',
            '--body-bg': '#212529',
            '--sidebar-bg': '#2a2e32',
            '--content-bg': '#343a40',
            '--text-primary': '#f8f9fa',
            '--text-secondary': '#ced4da',
            '--text-light': '#adb5bd',
            '--border-color': '#495057'
        }
    },
    light: {
        name: '浅色模式',
        vars: {
            '--primary-color': '#3498db',
            '--primary-light': '#e3f2fd',
            '--primary-dark': '#1976d2',
            '--body-bg': '#ffffff',
            '--sidebar-bg': '#f8f9fa',
            '--content-bg': '#ffffff',
            '--text-primary': '#212529',
            '--text-secondary': '#6c757d',
            '--text-light': '#adb5bd',
            '--border-color': '#e9ecef'
        }
    },
    blue: {
        name: '蓝色主题',
        vars: {
            '--primary-color': '#3949ab',
            '--primary-light': '#e8eaf6',
            '--primary-dark': '#283593',
            '--body-bg': '#f5f7ff',
            '--sidebar-bg': '#eff1fa',
            '--content-bg': '#ffffff',
            '--text-primary': '#212529',
            '--text-secondary': '#6c757d',
            '--text-light': '#adb5bd',
            '--border-color': '#dee2e6'
        }
    },
    green: {
        name: '绿色主题',
        vars: {
            '--primary-color': '#2e7d32',
            '--primary-light': '#e8f5e9',
            '--primary-dark': '#1b5e20',
            '--body-bg': '#f5f8f5',
            '--sidebar-bg': '#edf5ed',
            '--content-bg': '#ffffff',
            '--text-primary': '#212529',
            '--text-secondary': '#6c757d',
            '--text-light': '#adb5bd',
            '--border-color': '#dee2e6'
        }
    }
};

/**
 * 初始化主题设置
 * 从本地存储加载用户偏好并应用
 */
function initTheme() {
    // 从localStorage获取保存的主题
    const savedTheme = localStorage.getItem('theme') || 'default';
    setTheme(savedTheme);
}

/**
 * 设置主题
 * @param {string} themeName - 主题名称
 */
function setTheme(themeName) {
    if (!THEMES[themeName]) {
        console.error(`Theme "${themeName}" not found.`);
        themeName = 'default';
    }
    
    // 保存到localStorage
    localStorage.setItem('theme', themeName);
    
    // 获取主题变量
    const theme = THEMES[themeName];
    
    // 移除所有主题类
    document.body.className = document.body.className
        .split(' ')
        .filter(c => !c.startsWith('theme-'))
        .join(' ');
    
    // 添加当前主题类
    document.body.classList.add(`theme-${themeName}`);
    
    // 应用CSS变量
    const root = document.documentElement;
    Object.keys(theme.vars).forEach(key => {
        root.style.setProperty(key, theme.vars[key]);
    });
    
    // 添加切换动画
    document.body.classList.add('theme-transition');
    setTimeout(() => {
        document.body.classList.remove('theme-transition');
    }, 1000);
    
    // 如果有主题下拉菜单，更新当前选中项
    const themeDropdown = document.querySelector('.theme-dropdown');
    if (themeDropdown) {
        themeDropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-theme') === themeName) {
                item.classList.add('active');
            }
        });
    }
}

// 导出到全局作用域
window.initTheme = initTheme;
window.setTheme = setTheme; 