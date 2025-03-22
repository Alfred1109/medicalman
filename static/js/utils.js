/**
 * 医疗数据分析系统工具函数库
 * 按功能模块化组织，提高代码复用性和可维护性
 */

// ===== 日期和时间处理函数 =====
const DateUtils = {
    /**
     * 格式化日期为指定格式
     * @param {Date|string} date - 日期对象或日期字符串
     * @param {string} format - 格式模板，如 'YYYY-MM-DD HH:mm:ss'
     * @returns {string} 格式化后的日期字符串
     */
    formatDate: function(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        
        const d = typeof date === 'string' ? new Date(date) : date;
        if (isNaN(d.getTime())) return 'Invalid Date';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },
    
    /**
     * 获取相对时间描述（如：3小时前，2天前）
     * @param {Date|string} date - 日期对象或日期字符串
     * @returns {string} 相对时间描述
     */
    getRelativeTime: function(date) {
        if (!date) return '';
        
        const d = typeof date === 'string' ? new Date(date) : date;
        if (isNaN(d.getTime())) return 'Invalid Date';
        
        const now = new Date();
        const diffMs = now - d;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        const diffMonth = Math.floor(diffDay / 30);
        const diffYear = Math.floor(diffMonth / 12);
        
        if (diffSec < 60) return `${diffSec}秒前`;
        if (diffMin < 60) return `${diffMin}分钟前`;
        if (diffHour < 24) return `${diffHour}小时前`;
        if (diffDay < 30) return `${diffDay}天前`;
        if (diffMonth < 12) return `${diffMonth}个月前`;
        return `${diffYear}年前`;
    },
    
    /**
     * 获取日期范围的开始和结束时间
     * @param {string} range - 日期范围类型：'today', 'yesterday', 'thisWeek', 'lastWeek', 'thisMonth', 'lastMonth'
     * @returns {Object} 包含开始和结束日期的对象
     */
    getDateRange: function(range) {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        let start, end;
        
        switch (range) {
            case 'today':
                start = today;
                end = new Date(today);
                end.setDate(end.getDate() + 1);
                break;
            case 'yesterday':
                start = new Date(today);
                start.setDate(start.getDate() - 1);
                end = today;
                break;
            case 'thisWeek':
                start = new Date(today);
                start.setDate(start.getDate() - start.getDay());
                end = new Date(start);
                end.setDate(end.getDate() + 7);
                break;
            case 'lastWeek':
                start = new Date(today);
                start.setDate(start.getDate() - start.getDay() - 7);
                end = new Date(start);
                end.setDate(end.getDate() + 7);
                break;
            case 'thisMonth':
                start = new Date(today.getFullYear(), today.getMonth(), 1);
                end = new Date(today.getFullYear(), today.getMonth() + 1, 1);
                break;
            case 'lastMonth':
                start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                end = new Date(today.getFullYear(), today.getMonth(), 1);
                break;
            default:
                start = today;
                end = new Date(today);
                end.setDate(end.getDate() + 1);
        }
        
        return {
            start: start,
            end: end
        };
    }
};

// ===== 数字和格式化函数 =====
const FormatUtils = {
    /**
     * 格式化数字，添加千位分隔符
     * @param {number} num - 要格式化的数字
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的数字字符串
     */
    formatNumber: function(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        
        return Number(num).toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },
    
    /**
     * 格式化百分比
     * @param {number} value - 要格式化的值（0-1之间）
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的百分比字符串
     */
    formatPercent: function(value, decimals = 1) {
        if (value === null || value === undefined || isNaN(value)) return '0%';
        
        return (value * 100).toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }) + '%';
    },
    
    /**
     * 格式化文件大小
     * @param {number} bytes - 文件大小（字节）
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的文件大小字符串
     */
    formatFileSize: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
    },
    
    /**
     * 截断文本并添加省略号
     * @param {string} text - 要截断的文本
     * @param {number} length - 最大长度
     * @returns {string} 截断后的文本
     */
    truncateText: function(text, length = 50) {
        if (!text) return '';
        
        return text.length > length ? text.substring(0, length) + '...' : text;
    },
    
    /**
     * 获取文件扩展名
     * @param {string} filename - 文件名
     * @returns {string} 文件扩展名
     */
    getFileExtension: function(filename) {
        if (!filename) return '';
        
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    }
};

// ===== DOM操作和UI工具函数 =====
const DOMUtils = {
    /**
     * 显示加载中状态
     * @param {string} selector - 目标元素选择器
     * @param {string} message - 加载提示信息
     */
    showLoading: function(selector, message = '加载中...') {
        const target = document.querySelector(selector);
        if (!target) return;
        
        const loadingHtml = `
            <div class="loading-overlay">
                <div class="text-center">
                    <div class="spinner"></div>
                    <div class="mt-2">${message}</div>
                </div>
            </div>
        `;
        
        target.style.position = 'relative';
        target.insertAdjacentHTML('beforeend', loadingHtml);
    },
    
    /**
     * 隐藏加载中状态
     * @param {string} selector - 目标元素选择器
     */
    hideLoading: function(selector) {
        const target = document.querySelector(selector);
        if (!target) return;
        
        const overlay = target.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    /**
     * 显示通知消息
     * @param {string} message - 通知消息
     * @param {string} type - 通知类型：'success', 'error', 'warning', 'info'
     * @param {number} duration - 显示时长（毫秒）
     */
    showNotification: function(message, type = 'info', duration = 3000) {
        // 确保通知容器存在
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-close">&times;</div>
            <div>${message}</div>
        `;
        
        // 添加关闭事件
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', function() {
            notification.remove();
        });
        
        // 添加到容器
        container.appendChild(notification);
        
        // 自动关闭
        setTimeout(function() {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    },
    
    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise} 复制操作的Promise
     */
    copyToClipboard: function(text) {
        return navigator.clipboard.writeText(text)
            .then(() => {
                this.showNotification('复制成功', 'success');
                return true;
            })
            .catch(err => {
                this.showNotification('复制失败: ' + err, 'error');
                return false;
            });
    }
};

// ===== 数据处理和API工具函数 =====
const DataUtils = {
    /**
     * 发送API请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} 请求Promise
     */
    fetchAPI: function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };
        
        const fetchOptions = { ...defaultOptions, ...options };
        
        // 如果是POST/PUT请求且有data，转换为JSON
        if (fetchOptions.data && ['POST', 'PUT', 'PATCH'].includes(fetchOptions.method)) {
            fetchOptions.body = JSON.stringify(fetchOptions.data);
            delete fetchOptions.data;
        }
        
        return fetch(url, fetchOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('API request failed:', error);
                DOMUtils.showNotification(`请求失败: ${error.message}`, 'error');
                throw error;
            });
    },
    
    /**
     * 获取URL参数
     * @param {string} name - 参数名
     * @returns {string|null} 参数值
     */
    getUrlParam: function(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },
    
    /**
     * 生成随机ID
     * @param {number} length - ID长度
     * @returns {string} 随机ID
     */
    generateId: function(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },
    
    /**
     * 深度克隆对象
     * @param {Object} obj - 要克隆的对象
     * @returns {Object} 克隆后的对象
     */
    deepClone: function(obj) {
        if (obj === null || typeof obj !== 'object') {
            return obj;
        }
        
        if (obj instanceof Date) {
            return new Date(obj.getTime());
        }
        
        if (obj instanceof Array) {
            return obj.map(item => this.deepClone(item));
        }
        
        if (obj instanceof Object) {
            const copy = {};
            Object.keys(obj).forEach(key => {
                copy[key] = this.deepClone(obj[key]);
            });
            return copy;
        }
        
        return obj;
    },
    
    /**
     * 计算数组总和
     * @param {Array} arr - 数值数组
     * @returns {number} 总和
     */
    sum: function(arr) {
        if (!arr || arr.length === 0) return 0;
        return arr.reduce((a, b) => a + (b || 0), 0);
    },
    
    /**
     * 计算数组平均值
     * @param {Array} arr - 数值数组
     * @returns {number} 平均值
     */
    average: function(arr) {
        if (!arr || arr.length === 0) return 0;
        return this.sum(arr) / arr.length;
    },
    
    /**
     * 计算数组中位数
     * @param {Array} arr - 数值数组
     * @returns {number} 中位数
     */
    median: function(arr) {
        if (!arr || arr.length === 0) return 0;
        
        const sorted = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        
        return sorted.length % 2 === 0
            ? (sorted[mid - 1] + sorted[mid]) / 2
            : sorted[mid];
    },
    
    /**
     * 分组数据
     * @param {Array} data - 原始数据
     * @param {string} groupKey - 分组字段
     * @returns {Object} 分组后的数据
     */
    groupBy: function(data, groupKey) {
        if (!data || !Array.isArray(data)) return {};
        
        return data.reduce((acc, item) => {
            const key = item[groupKey];
            if (!acc[key]) {
                acc[key] = [];
            }
            acc[key].push(item);
            return acc;
        }, {});
    }
};

// ===== 性能优化工具函数 =====
const PerformanceUtils = {
    /**
     * 防抖函数
     * @param {Function} func - 要执行的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} 防抖处理后的函数
     */
    debounce: function(func, wait = 300) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func - 要执行的函数
     * @param {number} limit - 限制时间（毫秒）
     * @returns {Function} 节流处理后的函数
     */
    throttle: function(func, limit = 300) {
        let inThrottle;
        return function(...args) {
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * 延迟执行函数
     * @param {Function} func - 要执行的函数
     * @param {number} delay - 延迟时间（毫秒）
     * @returns {Promise} 延迟执行的Promise
     */
    delay: function(func, delay = 1000) {
        return new Promise(resolve => {
            setTimeout(() => {
                const result = func();
                resolve(result);
            }, delay);
        });
    }
};

// ===== 图表工具函数 =====
const ChartUtils = {
    /**
     * 获取图表主题配置
     * @param {string} theme - 主题名称
     * @returns {Object} 图表主题配置
     */
    getChartTheme: function(theme = 'default') {
        const themes = {
            default: {
                color: ['#5b8db8', '#6fc0ba', '#f2c94c', '#f2994a', '#eb5757', '#9b51e0'],
                backgroundColor: 'transparent',
                textStyle: {
                    color: '#333'
                },
                title: {
                    textStyle: {
                        color: '#333'
                    }
                },
                line: {
                    itemStyle: {
                        borderWidth: 2
                    },
                    lineStyle: {
                        width: 2
                    },
                    symbolSize: 8
                }
            },
            dark: {
                color: ['#5b8db8', '#6fc0ba', '#f2c94c', '#f2994a', '#eb5757', '#9b51e0'],
                backgroundColor: 'transparent',
                textStyle: {
                    color: '#eee'
                },
                title: {
                    textStyle: {
                        color: '#eee'
                    }
                },
                line: {
                    itemStyle: {
                        borderWidth: 2
                    },
                    lineStyle: {
                        width: 2
                    },
                    symbolSize: 8
                }
            }
        };
        
        return themes[theme] || themes.default;
    },
    
    /**
     * 更新所有图表的主题
     * @param {string} theme - 主题名称
     */
    updateChartsTheme: function(theme) {
        if (window.echarts) {
            const chartTheme = this.getChartTheme(theme);
            const charts = window.echartsInstances || [];
            
            charts.forEach(chart => {
                if (chart && typeof chart.setOption === 'function') {
                    const option = chart.getOption();
                    const newOption = {
                        color: chartTheme.color,
                        textStyle: chartTheme.textStyle,
                        title: {
                            textStyle: chartTheme.title.textStyle
                        }
                    };
                    chart.setOption(newOption);
                }
            });
        }
    },
    
    /**
     * 注册图表实例
     * @param {Object} chart - ECharts实例
     */
    registerChart: function(chart) {
        if (!window.echartsInstances) {
            window.echartsInstances = [];
        }
        window.echartsInstances.push(chart);
    },
    
    /**
     * 销毁图表实例
     * @param {Object} chart - ECharts实例
     */
    destroyChart: function(chart) {
        if (chart && typeof chart.dispose === 'function') {
            chart.dispose();
        }
        
        if (window.echartsInstances) {
            const index = window.echartsInstances.indexOf(chart);
            if (index > -1) {
                window.echartsInstances.splice(index, 1);
            }
        }
    },
    
    /**
     * 生成随机颜色数组
     * @param {number} count - 需要的颜色数量
     * @returns {Array} 颜色数组
     */
    generateColors: function(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 137) % 360; // 使用黄金角生成分散的颜色
            colors.push(`hsl(${hue}, 70%, 60%)`);
        }
        return colors;
    },
    
    /**
     * 获取渐变背景
     * @param {Object} ctx - Canvas上下文
     * @param {string} color - 基础颜色
     * @returns {Object} 渐变对象
     */
    getGradient: function(ctx, color) {
        const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.1)');
        return gradient;
    },
    
    /**
     * 将数据格式化为图表所需的格式
     * @param {Array} data - 原始数据
     * @param {string} labelKey - 标签字段名
     * @param {string} valueKey - 值字段名
     * @returns {Object} 格式化后的图表数据
     */
    formatChartData: function(data, labelKey, valueKey) {
        const labels = data.map(item => item[labelKey]);
        const values = data.map(item => item[valueKey]);
        
        return {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: this.generateColors(values.length)
            }]
        };
    }
};

// 导出所有工具函数
const Utils = {
    date: DateUtils,
    format: FormatUtils,
    dom: DOMUtils,
    data: DataUtils,
    performance: PerformanceUtils,
    chart: ChartUtils
};

// 全局暴露
window.Utils = Utils;

// 显示Toast消息
function showToast(type, message, duration = 3000) {
    // 删除已有的toast
    $('.toast').remove();
    
    // 创建toast元素
    const toast = `
        <div class="toast toast-${type}" role="alert">
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // 添加到页面
    $('body').append(toast);
    
    // 显示toast
    $('.toast').fadeIn();
    
    // 定时关闭
    setTimeout(function() {
        $('.toast').fadeOut(function() {
            $(this).remove();
        });
    }, duration);
} 