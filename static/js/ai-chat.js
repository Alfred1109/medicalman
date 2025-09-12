document.addEventListener('DOMContentLoaded', function() {
    console.log('AI聊天UI模块已加载');
    
    // 获取DOM元素
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const chatMessages = document.getElementById('chat-messages');
    const toggleKnowledgePanel = document.getElementById('toggleKnowledgePanel');
    const knowledgePanel = document.getElementById('knowledgePanel');
    const historyButton = document.getElementById('historyButton');
    const exportReportButton = document.getElementById('exportReport');
    
    if (!chatInput || !sendButton) {
        console.error('聊天界面缺少必要的DOM元素');
        return;
    }
    
    console.log('聊天UI元素加载完成，绑定事件');
    
    // 初始化模态框
    const historyModalEl = document.getElementById('historyModal');
    let historyModal = null;
    
    if (historyModalEl) {
        historyModal = new bootstrap.Modal(historyModalEl);
    }
    
    // 初始化知识库面板状态
    if (knowledgePanel) {
        knowledgePanel.style.display = 'none';
    }
    
    // ===== 事件绑定 =====
    
    // 知识库面板切换
    if (toggleKnowledgePanel) {
        console.log('正在绑定知识库按钮点击事件');
        toggleKnowledgePanel.onclick = function() {
            console.log('知识库按钮被点击');
            if (knowledgePanel) {
                knowledgePanel.style.display = knowledgePanel.style.display === 'none' ? 'block' : 'none';
                console.log('知识库面板显示状态切换为:', knowledgePanel.style.display);
            }
        };
    } else {
        console.error('找不到知识库切换按钮元素');
    }
    
    // 知识库面板关闭按钮
    const knowledgeToggle = document.querySelector('.knowledge-toggle');
    if (knowledgeToggle) {
        knowledgeToggle.addEventListener('click', function() {
            if (knowledgePanel) {
                knowledgePanel.style.display = 'none';
            }
        });
    }
    
    // 应用知识库设置
    const applyKnowledgeButton = document.getElementById('applyKnowledge');
    if (applyKnowledgeButton) {
        applyKnowledgeButton.addEventListener('click', function() {
            // 收集所有选中的知识库选项
            const knowledgeSettings = {
                tables: {
                    outpatient: document.getElementById('outpatient').checked,
                    target: document.getElementById('target').checked,
                    drg: document.getElementById('drg').checked
                },
                dimensions: {
                    department: document.getElementById('department').checked,
                    specialty: document.getElementById('specialty').checked,
                    target_completion: document.getElementById('target_completion').checked,
                    trend: document.getElementById('trend').checked
                },
                timeRange: document.getElementById('allTime').checked ? 'all' : 
                           document.getElementById('lastMonth').checked ? 'month' : 'week'
            };
            
            // 将设置保存到localStorage
            localStorage.setItem('knowledgeSettings', JSON.stringify(knowledgeSettings));
            
            // 显示提示
            alert('知识库设置已应用！');
        });
    }
    
    // 历史记录按钮
    if (historyButton) {
        console.log('正在绑定历史记录按钮点击事件');
        historyButton.onclick = function() {
            console.log('历史记录按钮被点击');
            if (historyModal) {
                historyModal.show();
                console.log('显示历史记录模态框');
            } else {
                console.error('历史记录模态框未初始化');
                // 创建一个简单的弹出对话框
                alert('历史记录功能暂时不可用，请稍后再试');
            }
        };
    } else {
        console.error('找不到历史记录按钮元素');
    }
    
    // 清空历史记录按钮
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
                const historyList = document.getElementById('historyList');
                historyList.innerHTML = '<div class="text-center p-3 text-muted">没有历史记录</div>';
            }
        });
    }
    
    // 清空聊天记录按钮
    if (clearButton) {
        console.log('正在绑定清空聊天按钮点击事件');
        clearButton.addEventListener('click', function() {
            console.log('清空聊天按钮被点击');
            if (confirm('确定要清空所有聊天记录吗？')) {
                chatMessages.innerHTML = '';
                displaySystemMessage('聊天记录已清空');
            }
        });
    } else {
        console.error('找不到清空聊天按钮元素');
    }
    
    // 导出报告按钮事件 - 仅当按钮存在时绑定
    if (exportReportButton) {
        console.log('正在绑定导出报告按钮点击事件');
        exportReportButton.addEventListener('click', function() {
            // 获取对话标题
            let title = prompt('请输入导出报告的标题:', '医疗分析对话报告');
            if (!title) {
                return; // 用户取消
            }
            
            // 调用导出函数
            exportChatReport(title);
        });
    } else {
        console.log('导出报告按钮不存在，跳过绑定事件');
    }
    
    // 发送按钮点击事件
    sendButton.addEventListener('click', function() {
        sendUserMessage();
    });
    
    // 输入框回车事件
    chatInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendUserMessage();
        }
    });
    
    // 点击聊天建议
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('chat-suggestion')) {
            chatInput.value = e.target.textContent;
            sendButton.click(); // 触发发送按钮点击事件
        }
    });
    
    // 页面加载时加载设置
    loadKnowledgeSettings();
    
    // 添加欢迎消息
    setTimeout(function() {
        addBotMessage('您好！我是医疗管理助手。请问有什么可以帮助您的？', []);
    }, 500);
});

/**
 * 获取当前知识库设置
 * @returns {Object} 知识库设置对象
 */
function getKnowledgeSettings() {
    // 获取数据源
    let dataSource = 'auto';
    const sourceRadios = document.querySelectorAll('input[name="data-source"]');
    sourceRadios.forEach(radio => {
        if (radio.checked) {
            dataSource = radio.value;
        }
    });
    
    // 构建知识库设置对象
    return {
        data_source: dataSource,
        tables: {
            outpatient: document.getElementById('outpatient')?.checked || false,
            target: document.getElementById('target')?.checked || false,
            drg: document.getElementById('drg')?.checked || false
        },
        dimensions: {
            department: document.getElementById('department')?.checked || false,
            specialty: document.getElementById('specialty')?.checked || false,
            target_completion: document.getElementById('target_completion')?.checked || false,
            trend: document.getElementById('trend')?.checked || false
        },
        time_range: document.getElementById('allTime')?.checked ? 'all' : 
                    document.getElementById('lastMonth')?.checked ? 'month' : 'week'
    };
}

// 导出到全局作用域
window.getKnowledgeSettings = getKnowledgeSettings;

/**
 * 从localStorage加载知识库设置
 */
function loadKnowledgeSettings() {
    try {
        const savedSettings = localStorage.getItem('knowledgeSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            // 应用数据源设置
            if (settings.dataSource) {
                const radioElement = document.getElementById(`${settings.dataSource}Source`);
                if (radioElement) {
                    radioElement.checked = true;
                }
            }
            
            // 应用表设置
            if (settings.tables) {
                for (const [table, checked] of Object.entries(settings.tables)) {
                    const checkbox = document.getElementById(table);
                    if (checkbox) {
                        checkbox.checked = checked;
                    }
                }
            }
            
            // 应用维度设置
            if (settings.dimensions) {
                for (const [dimension, checked] of Object.entries(settings.dimensions)) {
                    const checkbox = document.getElementById(dimension);
                    if (checkbox) {
                        checkbox.checked = checked;
                    }
                }
            }
            
            // 应用时间范围设置
            if (settings.timeRange) {
                const radioId = settings.timeRange === 'all' ? 'allTime' : 
                               settings.timeRange === 'month' ? 'lastMonth' : 'lastWeek';
                const radioElement = document.getElementById(radioId);
                if (radioElement) {
                    radioElement.checked = true;
                }
            }
            
            console.log('已从localStorage加载知识库设置');
        }
    } catch (error) {
        console.error('加载知识库设置时出错:', error);
    }
}

// 发送用户消息
function sendUserMessage() {
    // 获取用户输入
    const chatInput = document.getElementById('chat-input');
    if (!chatInput) {
        console.error('未找到聊天输入框元素');
        return;
    }
    
    const userInput = chatInput.value.trim();
    if (!userInput) return;
    
    // 清空输入框
    chatInput.value = '';
    
    // 检查ChatAPI是否可用
    if (!window.ChatAPI || typeof window.ChatAPI.sendMessage !== 'function') {
        console.error('聊天API未正确加载');
        displaySystemMessage('无法发送消息，聊天服务未正确加载');
        return;
    }
    
    // 添加用户消息到UI
    const userMessageId = 'msg-' + Date.now();
    addUserMessage(userInput, userMessageId);
    
    // 显示思考中的指示器
    displayThinking();
    
    // 获取知识库设置
    let knowledgeSettings = {};
    if (typeof getKnowledgeSettings === 'function') {
        knowledgeSettings = getKnowledgeSettings();
    }
    
    // 发送消息到后端
    window.ChatAPI.sendMessage(userInput, function(error, response) {
        // 隐藏思考中的指示器
        hideThinking();
        
        if (error) {
            console.error('发送消息失败:', error);
            displaySystemMessage('消息发送失败：' + (error.message || '未知错误'));
            return;
        }
        
        console.log('收到回复:', response);
        
        // 统一查找消息内容的逻辑
        let messageContent = null;
        let chartsData = null;
        let tablesData = null;
        
        // 按优先级查找消息内容
        if (response) {
            // 1. 优先检查answer字段（标准统一字段）
            if (response.answer) {
                messageContent = response.answer;
            } 
            // 2. 如果没有answer，检查message字段
            else if (response.message) {
                messageContent = response.message;
            }
            // 3. 其他可能的字段
            else if (response.text) {
                messageContent = response.text;
            } else if (typeof response === 'string') {
                messageContent = response;
            }
            
            // 按统一路径查找图表数据
            if (response.charts && Array.isArray(response.charts)) {
                chartsData = response.charts;
            } else if (response.data && response.data.charts && Array.isArray(response.data.charts)) {
                chartsData = response.data.charts;
            }
            
            // 按统一路径查找表格数据
            if (response.tables && Array.isArray(response.tables)) {
                tablesData = response.tables;
            } else if (response.data && response.data.tables && Array.isArray(response.data.tables)) {
                tablesData = response.data.tables;
            }
        }
        
        // 处理消息内容
        if (messageContent) {
            // 添加AI回复到UI
            addBotMessage(messageContent, chartsData || []);
            
            // 处理表格数据
            if (tablesData && tablesData.length > 0) {
                handleTablesData(tablesData);
            }
        } else {
            // 无法识别的响应格式
            console.error('无法识别的响应格式:', response);
            
            // 尝试将响应转换为可读文本
            try {
                const responseStr = JSON.stringify(response, null, 2);
                addBotMessage(`服务器响应数据:\n\`\`\`json\n${responseStr}\n\`\`\``, []);
            } catch (e) {
                displaySystemMessage('收到无法识别的响应');
            }
        }
    });
}

/**
 * 将用户消息添加到聊天界面
 * @param {string} message - 用户消息内容
 * @param {string} messageId - 消息ID用于后续引用
 */
function addUserMessage(message, messageId) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = 'message user-message';
    
    // 格式化消息内容，支持换行
    const formattedMessage = message.replace(/\n/g, '<br>');
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-sender">您</span>
            <span class="message-time">${formatTime(new Date())}</span>
        </div>
        <div class="message-content">${formattedMessage}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

/**
 * 将AI回复添加到聊天界面
 * @param {string} message - AI回复内容
 * @param {Array} charts - 图表数据（如果有）
 */
function addBotMessage(message, charts) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    
    // 格式化消息内容，支持Markdown
    const messageContent = formatMarkdown(message);
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-sender">AI助手</span>
            <span class="message-time">${formatTime(new Date())}</span>
        </div>
        <div class="message-content">${messageContent}</div>
    `;
    
    // 如果有图表数据，添加图表容器
    if (charts && charts.length > 0) {
        const chartsContainer = document.createElement('div');
        chartsContainer.className = 'charts-container';
        
        charts.forEach((chart, index) => {
            const chartElement = document.createElement('div');
            chartElement.className = 'chart';
            chartElement.id = `chart-${Date.now()}-${index}`;
            chartElement.style.height = '300px';
            chartsContainer.appendChild(chartElement);
            
            // 延迟渲染图表，确保DOM已经准备好
            setTimeout(() => {
                renderChart(chartElement.id, chart);
            }, 100);
        });
        
        messageElement.appendChild(chartsContainer);
    }
    
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

/**
 * 显示系统消息
 * @param {string} message - 系统消息内容
 */
function displaySystemMessage(message) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = 'message system-message';
    
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

/**
 * 显示"思考中"的指示器
 */
function displayThinking() {
    const messagesContainer = document.getElementById('chat-messages');
    const thinkingElement = document.createElement('div');
    thinkingElement.id = 'thinking-indicator';
    thinkingElement.className = 'message bot-message thinking';
    
    thinkingElement.innerHTML = `
        <div class="message-header">
            <span class="message-sender">AI助手</span>
            <span class="message-time">${formatTime(new Date())}</span>
        </div>
        <div class="message-content">
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(thinkingElement);
    scrollToBottom();
}

/**
 * 隐藏"思考中"的指示器
 */
function hideThinking() {
    const thinkingIndicator = document.getElementById('thinking-indicator');
    if (thinkingIndicator) {
        thinkingIndicator.remove();
    }
}

/**
 * 格式化时间为HH:MM格式
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的时间字符串
 */
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * 滚动到聊天窗口底部
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * 格式化Markdown内容为HTML
 * @param {string} markdown - Markdown格式的文本
 * @returns {string} 转换后的HTML
 */
function formatMarkdown(markdown) {
    // 这里简化处理，只转换代码块和换行
    let html = markdown;
    
    // 处理代码块
    html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
    
    // 处理换行
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

/**
 * 渲染Vega-Lite图表（使用VegaChartUtils）
 * @param {string} elementId - 图表容器元素ID
 * @param {Object} chartData - Vega-Lite规范数据
 */
function renderChart(elementId, chartData) {
    // 优先使用VegaChartUtils
    if (typeof VegaChartUtils !== 'undefined') {
        return VegaChartUtils.render(elementId, chartData)
            .then(result => {
                console.log('Vega-Lite图表渲染成功:', result);
                return result;
            })
            .catch(error => {
                console.error('使用VegaChartUtils渲染图表失败:', error);
                // 不抛出错误，让调用者处理
                return null;
            });
    }
    
    // 备用方案：直接使用vega-embed
    if (typeof vegaEmbed === 'undefined') {
        console.error('VegaChartUtils和vega-embed都不可用，无法渲染图表');
        return Promise.reject(new Error('图表渲染器不可用'));
    }

    const chartElement = document.getElementById(elementId);
    if (!chartElement) {
        const error = new Error(`未找到图表容器元素: ${elementId}`);
        console.error(error.message);
        return Promise.reject(error);
    }

    try {
        // 确保有schema
        if (!chartData.$schema) {
            chartData.$schema = "https://vega.github.io/schema/vega-lite/v5.json";
        }
        
        // 添加医疗主题配置
        if (!chartData.config) {
            chartData.config = {
                axis: {
                    labelFontSize: 11,
                    titleFontSize: 12,
                    titleFontWeight: "bold"
                },
                title: {
                    fontSize: 16,
                    fontWeight: "bold",
                    color: "#333"
                },
                legend: {
                    labelFontSize: 11,
                    titleFontSize: 12
                }
            };
        }
        
        // Vega-Embed选项
        const embedOptions = {
            theme: 'quartz',
            tooltip: {
                theme: 'dark'
            },
            actions: {
                export: true,
                source: false,
                compiled: false,
                editor: false
            }
        };
        
        // 渲染图表
        return vegaEmbed(chartElement, chartData, embedOptions)
            .then(result => {
                console.log('Vega-Lite图表渲染成功:', result);
                
                // 存储视图引用以便后续操作
                chartElement._vegaView = result.view;
                
                return result;
            })
            .catch(error => {
                console.error('渲染Vega-Lite图表时出错:', error);
                console.error('图表数据:', chartData);
                
                // 显示错误信息
                chartElement.innerHTML = `
                    <div class="alert alert-warning" style="margin: 10px; padding: 15px;">
                        <h6><i class="fas fa-exclamation-triangle"></i> 图表渲染失败</h6>
                        <small>${error.message || '未知错误'}</small>
                    </div>
                `;
                
                throw error; // 重新抛出错误让调用者处理
            });
        
    } catch (error) {
        console.error('渲染图表时出错:', error);
        console.error('图表数据:', chartData);
        
        // 显示错误信息
        const chartElement = document.getElementById(elementId);
        if (chartElement) {
            chartElement.innerHTML = `
                <div class="alert alert-danger" style="margin: 10px; padding: 15px;">
                    <h6><i class="fas fa-times-circle"></i> 图表渲染失败</h6>
                    <small>${error.message || '未知错误'}</small>
                </div>
            `;
        }
        
        return Promise.reject(error);
    }
}

/**
 * 导出聊天记录为报告
 * @param {string} title - 报告标题
 */
function exportChatReport(title) {
    // 显示加载指示
    displaySystemMessage('正在生成报告...');
    
    try {
        // 获取所有消息
        const messages = [];
        const messageElements = document.querySelectorAll('.message');
        
        messageElements.forEach(element => {
            // 跳过系统消息和思考中状态
            if (element.classList.contains('system-message') || 
                element.classList.contains('thinking')) {
                return;
            }
            
            const isUser = element.classList.contains('user-message');
            const contentEl = element.querySelector('.message-content');
            
            if (contentEl) {
                // 获取消息内容
                const content = contentEl.innerHTML;
                
                // 查找图表
                const charts = [];
                const chartElements = element.querySelectorAll('.chart');
                chartElements.forEach(chartEl => {
                    if (chartEl.id) {
                        charts.push({
                            id: chartEl.id,
                            type: 'chart'
                        });
                    }
                });
                
                messages.push({
                    role: isUser ? 'user' : 'assistant',
                    content: content,
                    charts: charts
                });
            }
        });
        
        // 准备报告数据
        const reportData = {
            title: title,
            timestamp: new Date().toISOString(),
            messages: messages
        };
        
        // 发送到服务器生成报告
        fetch('/chat/export_chat_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.ChatAPI.getCsrfToken()
            },
            body: JSON.stringify(reportData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误! 状态: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `${title.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            
            // 清理
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            displaySystemMessage('报告已生成，正在下载...');
        })
        .catch(error => {
            console.error('导出报告失败:', error);
            displaySystemMessage('导出报告失败: ' + error.message);
        });
    } catch (error) {
        console.error('生成报告时出错:', error);
        displaySystemMessage('生成报告失败: ' + error.message);
    }
}

/**
 * 处理表格数据，在聊天消息中渲染表格
 * @param {Array} tables - 表格数据数组
 */
function handleTablesData(tables) {
    if (!tables || !Array.isArray(tables) || tables.length === 0) {
        return;
    }
    
    // 获取最后一条AI消息
    const messagesContainer = document.getElementById('chat-messages');
    const lastBotMessage = messagesContainer.querySelector('.bot-message:last-child');
    
    if (!lastBotMessage) {
        console.error('未找到AI消息元素，无法添加表格');
        return;
    }
    
    // 获取消息内容元素
    const messageContent = lastBotMessage.querySelector('.message-content');
    
    // 为每个表格创建HTML
    tables.forEach((table, index) => {
        // 检查表格数据的有效性
        if (!table.headers || !table.rows) {
            console.error(`表格数据 #${index+1} 格式无效`, table);
            return;
        }
        
        // 创建表格容器
        const tableContainer = document.createElement('div');
        tableContainer.className = 'data-table-container';
        
        // 添加表格标题（如果有）
        if (table.title) {
            const titleElement = document.createElement('h4');
            titleElement.textContent = table.title;
            tableContainer.appendChild(titleElement);
        }
        
        // 创建表格元素
        const tableElement = document.createElement('table');
        tableElement.className = 'data-table';
        
        // 创建表头
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        table.headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        tableElement.appendChild(thead);
        
        // 创建表格内容
        const tbody = document.createElement('tbody');
        
        table.rows.forEach(row => {
            const tr = document.createElement('tr');
            
            // 处理行数据
            if (Array.isArray(row)) {
                // 行是数组形式
                row.forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell !== null && cell !== undefined ? cell.toString() : '';
                    tr.appendChild(td);
                });
            } else if (typeof row === 'object') {
                // 行是对象形式，按表头顺序显示
                table.headers.forEach(header => {
                    const td = document.createElement('td');
                    const value = row[header];
                    td.textContent = value !== null && value !== undefined ? value.toString() : '';
                    tr.appendChild(td);
                });
            }
            
            tbody.appendChild(tr);
        });
        
        tableElement.appendChild(tbody);
        tableContainer.appendChild(tableElement);
        
        // 将表格添加到消息内容后
        messageContent.appendChild(tableContainer);
    });
    
    // 滚动到底部确保表格可见
    scrollToBottom();
} 