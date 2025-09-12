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

// ===== 数据缓存和管理 =====
const DataCache = {
    /**
     * 设置缓存数据
     * @param {string} key - 缓存键
     * @param {*} data - 要缓存的数据
     * @param {number} expirationMs - 过期时间(毫秒)
     */
    set: function(key, data, expirationMs = 300000) { // 默认5分钟
        try {
            const item = {
                data: data,
                expiry: Date.now() + expirationMs
            };
            localStorage.setItem(`api_cache:${key}`, JSON.stringify(item));
        } catch (e) {
            console.error('缓存数据失败:', e);
        }
    },
    
    /**
     * 获取缓存数据
     * @param {string} key - 缓存键
     * @returns {*} 缓存的数据，如果过期或不存在则返回null
     */
    get: function(key) {
        try {
            const item = localStorage.getItem(`api_cache:${key}`);
            if (!item) return null;
            
            const parsedItem = JSON.parse(item);
            if (Date.now() > parsedItem.expiry) {
                this.remove(key);
                return null;
            }
            
            return parsedItem.data;
        } catch (e) {
            this.remove(key);
            return null;
        }
    },
    
    /**
     * 删除缓存数据
     * @param {string} key - 缓存键
     */
    remove: function(key) {
        localStorage.removeItem(`api_cache:${key}`);
    },
    
    /**
     * 清空所有缓存数据
     */
    clear: function() {
        Object.keys(localStorage)
            .filter(key => key.startsWith('api_cache:'))
            .forEach(key => localStorage.removeItem(key));
    }
};

// ===== 增强型图表工具函数 =====
const ChartUtils = {
    // 存储已注册的Vega-Lite视图
    vegaViews: {},
    
    /**
     * 注册图表实例
     * @param {string} id - 图表ID
     * @param {Object} chart - 图表实例
     */
    registerChart: function(id, chart) {
        if (!id || !chart) return;
        
        // 如果已存在同ID图表，先清除
        if (this.chartInstances[id]) {
            this.chartInstances[id].dispose();
        }
        
        // 注册新图表
        this.chartInstances[id] = chart;
        console.log(`图表已注册: ${id}`);
        
        // 添加窗口调整大小时自动调整图表
        if (!this._resizeListenerAdded) {
            window.addEventListener('resize', this.resizeAllCharts.bind(this));
            this._resizeListenerAdded = true;
        }
    },
    
    /**
     * 获取已注册的图表
     * @param {string} id - 图表ID
     * @returns {Object} 图表实例
     */
    getChart: function(id) {
        return this.chartInstances[id];
    },
    
    /**
     * 调整所有图表大小
     */
    resizeAllCharts: function() {
        Object.values(this.chartInstances).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    },
    
    /**
     * 清除特定图表
     * @param {string} id - 图表ID
     */
    clearChart: function(id) {
        if (this.chartInstances[id]) {
            this.chartInstances[id].dispose();
            delete this.chartInstances[id];
        }
    },
    
    /**
     * 清除所有图表
     */
    clearAllCharts: function() {
        Object.keys(this.chartInstances).forEach(id => {
            if (this.chartInstances[id]) {
                this.chartInstances[id].dispose();
            }
        });
        this.chartInstances = {};
    },
    
    /**
     * 统一的图表初始化函数，支持更多选项和错误处理
     * @param {string|HTMLElement} container - 图表容器ID或DOM元素
     * @param {Object} options - ECharts配置选项
     * @param {boolean} forceCreate - 是否强制创建新实例（忽略已有实例）
     * @param {Object} fallbackData - 如果初始化失败，使用的备用数据
     * @returns {Object} ECharts实例
     */
    initChart: function(container, options, forceCreate = false, fallbackData = null) {
        try {
            // 规范化容器参数
            let containerElement;
            if (typeof container === 'string') {
                containerElement = document.getElementById(container);
            } else {
                containerElement = container;
            }
            
            // 验证容器存在
            if (!containerElement) {
                console.error(`图表容器未找到: ${container}`);
                return null;
            }
            
            // 确保容器有ID
            const containerId = containerElement.id || `chart-container-${Date.now()}`;
            if (!containerElement.id) {
                containerElement.id = containerId;
            }
            
            // 如果不强制创建且已有实例，则返回现有实例
            if (!forceCreate && this.chartInstances[containerId]) {
                const instance = this.chartInstances[containerId];
                instance.setOption(options, true);
                return instance;
            }
            
            // 清除可能存在的旧实例
            if (this.chartInstances[containerId]) {
                this.chartInstances[containerId].dispose();
            }
            
            // 创建新实例
            const chartInstance = echarts.init(containerElement);
            chartInstance.setOption(options);
            
            // 保存实例引用
            this.chartInstances[containerId] = chartInstance;
            
            // 添加窗口大小调整监听
            if (!this._resizeListenerAdded) {
                window.addEventListener('resize', this._handleResize.bind(this));
                this._resizeListenerAdded = true;
            }
            
            // 添加自动清理
            this._setupAutoCleanup(containerElement, containerId);
            
            return chartInstance;
        } catch (error) {
            console.error(`初始化图表失败: ${error.message}`, error);
            
            // 如果提供了备用数据，尝试使用它
            if (fallbackData) {
                try {
                    const containerElement = typeof container === 'string' ? 
                        document.getElementById(container) : container;
                    
                    if (containerElement) {
                        // 显示错误信息
                        containerElement.innerHTML = `
                            <div class="chart-error">
                                <p>图表加载失败</p>
                                <p class="text-muted small">${error.message}</p>
                            </div>
                        `;
                    }
                } catch (fallbackError) {
                    console.error('使用备用数据失败', fallbackError);
                }
            }
            
            return null;
        }
    },
    
    /**
     * 更新图表数据
     * @param {string|Object} chart - 图表ID或图表实例
     * @param {Object} options - 新的ECharts配置选项
     * @param {boolean} notMerge - 是否不合并配置（完全替换）
     * @returns {boolean} 操作成功状态
     */
    updateChart: function(chart, options, notMerge = false) {
        try {
            let chartInstance;
            
            // 获取图表实例
            if (typeof chart === 'string') {
                chartInstance = this.chartInstances[chart] || 
                                echarts.getInstanceByDom(document.getElementById(chart));
            } else {
                chartInstance = chart;
            }
            
            if (!chartInstance) {
                console.error('更新图表失败：找不到图表实例');
                return false;
            }
            
            // 更新配置
            chartInstance.setOption(options, notMerge);
            return true;
        } catch (error) {
            console.error(`更新图表失败: ${error.message}`, error);
            return false;
        }
    },
    
    /**
     * 处理窗口大小调整，自动重新绘制所有图表
     * @private
     */
    _handleResize: function() {
        // 使用节流函数，防止频繁调整大小时过多重绘
        if (this._resizeTimer) {
            clearTimeout(this._resizeTimer);
        }
        
        this._resizeTimer = setTimeout(() => {
            Object.values(this.chartInstances).forEach(chart => {
                if (chart && !chart.isDisposed()) {
                    chart.resize();
                }
            });
        }, 200);
    },
    
    /**
     * 为图表容器设置自动清理，避免内存泄漏
     * @param {HTMLElement} container - 图表容器
     * @param {string} containerId - 容器ID
     * @private
     */
    _setupAutoCleanup: function(container, containerId) {
        // 使用MutationObserver监听DOM变化，检测容器何时被移除
        if (!this._observer) {
            this._observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.removedNodes.forEach(node => {
                        // 检查移除的节点是否包含任何图表容器
                        Object.keys(this.chartInstances).forEach(id => {
                            try {
                                const element = document.getElementById(id);
                                if (!element || node.contains(element)) {
                                    // 容器已移除，销毁图表实例
                                    const chart = this.chartInstances[id];
                                    if (chart && !chart.isDisposed()) {
                                        chart.dispose();
                                    }
                                    delete this.chartInstances[id];
                                }
                            } catch (e) {
                                console.warn(`清理图表${id}时出错:`, e);
                            }
                        });
                    });
                });
            });
            
            // 开始监听document.body的变化
            this._observer.observe(document.body, { 
                childList: true,
                subtree: true
            });
        }
    },
    
    /**
     * 销毁指定图表
     * @param {string|Object} chart - 图表ID或图表实例
     */
    destroyChart: function(chart) {
        try {
            let chartInstance, chartId;
            
            if (typeof chart === 'string') {
                chartId = chart;
                chartInstance = this.chartInstances[chartId];
            } else {
                chartInstance = chart;
                // 查找实例的ID
                chartId = Object.keys(this.chartInstances).find(id => 
                    this.chartInstances[id] === chartInstance
                );
            }
            
            if (chartInstance && !chartInstance.isDisposed()) {
                chartInstance.dispose();
            }
            
            if (chartId) {
                delete this.chartInstances[chartId];
            }
        } catch (error) {
            console.error(`销毁图表失败: ${error.message}`, error);
        }
    },
    
    /**
     * 清除所有图表实例
     */
    destroyAllCharts: function() {
        Object.values(this.chartInstances).forEach(chart => {
            if (chart && !chart.isDisposed()) {
                try {
                    chart.dispose();
                } catch (e) {
                    console.warn('销毁图表时出错:', e);
                }
            }
        });
        
        this.chartInstances = {};
    },
    
    /**
     * 生成图表的备用数据，当API请求失败时使用
     * @param {string} chartType - 图表类型
     * @param {Object} options - 选项（数据点数量等）
     * @returns {Object} 备用数据
     */
    generateFallbackData: function(chartType, options = {}) {
        const pointCount = options.pointCount || 7;
        const maxValue = options.maxValue || 100;
        const categories = options.categories || ['类别A', '类别B', '类别C', '类别D', '类别E'];
        
        switch (chartType) {
            case 'line':
                // 生成折线图数据
                const dates = [];
                const values = [];
                const now = new Date();
                
                for (let i = 0; i < pointCount; i++) {
                    const date = new Date(now);
                    date.setDate(date.getDate() - (pointCount - i - 1));
                    dates.push(date.toISOString().split('T')[0]);
                    values.push(Math.floor(Math.random() * maxValue));
                }
                
                return {
                    xAxis: {
                        type: 'category',
                        data: dates
                    },
                    series: [{
                        name: '模拟数据',
                        data: values
                    }]
                };
                
            case 'bar':
                // 生成柱状图数据
                return {
                    xAxis: {
                        type: 'category',
                        data: categories.slice(0, pointCount)
                    },
                    series: [{
                        name: '模拟数据',
                        data: Array.from({length: pointCount}, () => Math.floor(Math.random() * maxValue))
                    }]
                };
                
            case 'pie':
                // 生成饼图数据
                const pieData = categories.slice(0, pointCount).map(category => ({
                    name: category,
                    value: Math.floor(Math.random() * maxValue)
                }));
                
                return {
                    series: [{
                        name: '模拟数据',
                        data: pieData
                    }]
                };
                
            default:
                return null;
        }
    }
};

/**
 * API 请求工具函数
 * 提供统一的API调用方法，自动添加CSRF令牌和处理常见错误
 */
const ApiUtils = {
    /**
     * 获取CSRF令牌
     * @returns {string} CSRF令牌
     */
    getCsrfToken() {
        // 1. 尝试从meta标签获取
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        if (tokenElement && tokenElement.content) {
            return tokenElement.content;
        }
        
        // 2. 尝试从cookie获取
        try {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith('csrf_token=')) {
                    return cookie.substring('csrf_token='.length, cookie.length);
                }
            }
        } catch (e) {
            console.warn('从cookie获取CSRF token失败:', e);
        }
        
        console.warn('无法获取CSRF token');
        return '';
    },
    
    /**
     * 发送API请求
     * @param {string} url - 请求URL
     * @param {string} method - HTTP方法(GET, POST, PUT, DELETE)
     * @param {Object} data - 请求数据(对象)
     * @param {Object} options - 额外选项
     * @returns {Promise} 请求Promise
     */
    async sendRequest(url, method = 'GET', data = null, options = {}) {
        const csrfToken = this.getCsrfToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // 添加CSRF令牌
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const fetchOptions = {
            method,
            headers,
            credentials: 'same-origin',
            ...options
        };
        
        // 添加请求体
        if (data && method !== 'GET') {
            fetchOptions.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, fetchOptions);
            
            // 检查响应状态
            if (!response.ok) {
                // 尝试解析错误响应
                const errorData = await response.json().catch(() => null);
                
                // 创建错误对象
                const error = new Error(errorData?.message || `HTTP error ${response.status}`);
                error.status = response.status;
                error.data = errorData;
                throw error;
            }
            
            // 解析JSON响应
            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            // 重新抛出以便调用者处理
            throw error;
        }
    },
    
    /**
     * GET请求
     * @param {string} url - 请求URL
     * @param {Object} params - 请求参数
     * @param {boolean} useCache - 是否使用缓存
     * @returns {Promise} 请求Promise
     */
    async get(url, params = {}, useCache = true) {
        // 如果使用缓存，先尝试从缓存获取
        if (useCache) {
            const cacheKey = url + JSON.stringify(params);
            const cachedData = DataCache.get(cacheKey);
            if (cachedData) {
                console.log('使用缓存数据:', cacheKey);
                return cachedData;
            }
        }
        
        // 无缓存或缓存过期，发送请求
        const result = await this.sendRequest(url, 'GET', null, params);
        
        // 请求成功时缓存结果
        if (useCache && result) {
            const cacheKey = url + JSON.stringify(params);
            DataCache.set(cacheKey, result, 5 * 60 * 1000); // 5分钟缓存
        }
        
        return result;
    },
    
    /**
     * POST请求
     * @param {string} url - 请求URL
     * @param {Object} data - 请求数据
     * @param {Object} options - 请求选项
     * @returns {Promise} 请求Promise
     */
    async post(url, data, options = {}) {
        const useCache = options.useCache !== undefined ? options.useCache : false;
        
        // 如果使用缓存，先尝试从缓存获取
        if (useCache) {
            const cacheKey = url + JSON.stringify(data);
            const cachedData = DataCache.get(cacheKey);
            if (cachedData) {
                console.log('使用缓存数据:', cacheKey);
                return cachedData;
            }
        }
        
        // 无缓存或缓存过期，发送请求
        const result = await this.sendRequest(url, 'POST', data, options);
        
        // 请求成功时缓存结果
        if (useCache && result) {
            const cacheKey = url + JSON.stringify(data);
            DataCache.set(cacheKey, result, 5 * 60 * 1000); // 5分钟缓存
        }
        
        return result;
    },
    
    /**
     * PUT请求
     * @param {string} url - 请求URL
     * @param {Object} data - 请求数据
     * @param {Object} options - 请求选项
     * @returns {Promise} 请求Promise
     */
    put(url, data, options = {}) {
        return this.sendRequest(url, 'PUT', data, options);
    },
    
    /**
     * DELETE请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} 请求Promise
     */
    delete(url, options = {}) {
        return this.sendRequest(url, 'DELETE', null, options);
    }
};

/**
 * 统一导出工具函数
 */
const Utils = {
    date: DateUtils,
    format: FormatUtils,
    dom: DOMUtils,
    data: DataUtils,
    performance: PerformanceUtils,
    chart: ChartUtils,
    api: ApiUtils,
    cache: DataCache,
    
    /**
     * 创建唯一ID
     * @returns {string} 唯一ID
     */
    generateId() {
        return '_' + Math.random().toString(36).substr(2, 9);
    },
    
    /**
     * 防抖函数
     * @param {Function} func - 要执行的函数
     * @param {number} wait - 延迟时间(毫秒)
     * @returns {Function} 防抖处理后的函数
     */
    debounce(func, wait = 300) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func - 要执行的函数
     * @param {number} limit - 时间间隔(毫秒)
     * @returns {Function} 节流处理后的函数
     */
    throttle(func, limit = 300) {
        let inThrottle;
        return function() {
            const context = this;
            const args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// ===== 添加其他全局工具函数 ===== 