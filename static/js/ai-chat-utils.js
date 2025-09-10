// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// 添加用户消息到聊天界面
function addUserMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const userMessageHTML = `
        <div class="chat-message user">
            <div class="chat-avatar user">
                <i class="fas fa-user"></i>
            </div>
            <div class="chat-bubble user">
                <div>${message}</div>
                <div class="chat-time">${getCurrentTime()}</div>
            </div>
        </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', userMessageHTML);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 向聊天区域添加新的AI消息
function addAIMessage(message, isLoading = false) {
    console.log(`添加AI消息: "${message}", isLoading=${isLoading}`);
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatMessages) {
        console.error('未找到chatMessages容器元素');
        return null;
    }
    
    // 创建消息容器
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';
    
    // 创建头像
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'chat-avatar ai';
    const avatarIcon = document.createElement('i');
    avatarIcon.className = 'fas fa-robot';
    avatarDiv.appendChild(avatarIcon);
    
    // 创建气泡
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'chat-bubble ai';
    if (isLoading) {
        console.log('添加思考中状态');
        bubbleDiv.classList.add('thinking');
    }
    
    // 创建消息内容
    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-content';
    
    if (isLoading) {
        // 创建一个容器来包含文本和动画
        const thinkingContainer = document.createElement('div');
        thinkingContainer.style.display = 'flex';
        thinkingContainer.style.alignItems = 'center';
        
        // 添加文本
        const textSpan = document.createElement('span');
        textSpan.textContent = '思考中';
        textSpan.id = 'ai-thinking-text';
        console.log('添加思考中文本');
        thinkingContainer.appendChild(textSpan);
        
        // 添加条状动画元素
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.textContent = '';
            typingIndicator.appendChild(dot);
        }
        console.log('添加思考中动画');
        thinkingContainer.appendChild(typingIndicator);
        
        // 将容器添加到内容div
        contentDiv.appendChild(thinkingContainer);
    } else {
        console.log('添加常规消息内容');
        try {
            // 解析Markdown
            const markdownDiv = document.createElement('div');
            markdownDiv.className = 'markdown-body';
            markdownDiv.innerHTML = parseMarkdown(message);
            contentDiv.appendChild(markdownDiv);
        } catch (e) {
            console.error('解析Markdown失败:', e);
            contentDiv.textContent = message;
        }
    }
    
    // 创建时间标记
    const timeDiv = document.createElement('div');
    timeDiv.className = 'chat-time';
    timeDiv.textContent = getCurrentTime();
    
    // 组装消息
    bubbleDiv.appendChild(contentDiv);
    bubbleDiv.appendChild(timeDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);
    
    // 添加到聊天区域并确认DOM更新
    chatMessages.appendChild(messageDiv);
    console.log('消息已添加到DOM');
    console.log('添加后的DOM结构:', messageDiv.outerHTML.substring(0, 200) + '...');
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// 更新AI消息
function updateAIMessage(message) {
    console.log('开始执行updateAIMessage函数');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatMessages) {
        console.error('无法找到聊天消息容器元素');
        return;
    }
    
    const allMessages = chatMessages.querySelectorAll('.chat-message');
    console.log(`当前聊天消息总数: ${allMessages.length}`);
    
    if (allMessages.length === 0) {
        console.error('未找到任何聊天消息');
        return;
    }
    
    const lastMessage = allMessages[allMessages.length - 1];
    console.log('找到最后一条消息:', lastMessage);
    
    if (lastMessage) {
        const bubble = lastMessage.querySelector('.chat-bubble.ai');
        console.log('找到AI气泡元素:', bubble);
        
        if (bubble && bubble.classList.contains('thinking')) {
            console.log('找到正在思考的AI气泡，准备更新内容');
            bubble.classList.remove('thinking');
            const contentDiv = bubble.querySelector('div:first-child');
            
            if (!contentDiv) {
                console.error('未找到内容DIV');
                return;
            }
            
            console.log('更新前的内容:', contentDiv.innerHTML);
            
            // 使用marked.js渲染Markdown内容
            try {
                console.log('将要渲染的Markdown内容:', message);
                const parsedContent = parseMarkdown(message);
                console.log('解析后的HTML内容:', parsedContent);
                contentDiv.innerHTML = `<div class="markdown-body">${parsedContent}</div>`;
                console.log('HTML内容已设置到DOM');
            } catch (error) {
                console.error('渲染Markdown时出错:', error);
                contentDiv.innerHTML = `<div class="markdown-body">${message}</div>`;
            }
            
            // 应用代码高亮
            try {
                const codeBlocks = bubble.querySelectorAll('.markdown-body pre code');
                console.log(`找到 ${codeBlocks.length} 个代码块，应用高亮`);
                codeBlocks.forEach((block) => {
                    hljs.highlightBlock(block);
                });
            } catch (error) {
                console.error('应用代码高亮时出错:', error);
            }
            
            // 更新时间
            const timeDiv = bubble.querySelector('.chat-time');
            if (timeDiv) {
                timeDiv.textContent = getCurrentTime();
                console.log('更新了时间戳');
            } else {
                console.warn('未找到时间元素');
            }
            
            console.log('DOM更新后的AI消息内容:', contentDiv.textContent.substring(0, 100) + '...');
        } else {
            console.warn('最后一条消息不是AI的思考气泡，无法更新');
            console.log('气泡类名:', bubble ? Array.from(bubble.classList).join(', ') : 'NULL');
        }
    } else {
        console.error('未找到最后一条消息');
    }
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    console.log('已滚动到聊天底部');
}

// 获取文件类型
function getFileType(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'pdf':
            return 'pdf';
        case 'docx':
        case 'doc':
            return 'word';
        case 'txt':
            return 'text';
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif':
            return 'image';
        default:
            return 'file';
    }
}

// 安全的解析Markdown内容
function parseMarkdown(text) {
    console.log('开始解析Markdown，输入文本长度:', text.length);
    console.log('输入文本前100个字符:', text.substring(0, 100));
    
    // 检查marked库是否可用
    if (typeof marked !== 'undefined') {
        try {
            console.log('使用marked.js解析Markdown');
            // 配置marked选项
            if (typeof marked.setOptions === 'function') {
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    sanitize: false,
                    highlight: function(code, lang) {
                        if (typeof hljs !== 'undefined' && hljs.getLanguage && hljs.getLanguage(lang)) {
                            return hljs.highlight(code, { language: lang }).value;
                        }
                        return code;
                    }
                });
            }
            
            // 使用marked.parse或marked（兼容不同版本）
            const result = (typeof marked.parse === 'function') ? 
                marked.parse(text) : marked(text);
            console.log('Markdown解析成功，输出HTML长度:', result.length);
            return result;
        } catch (e) {
            console.error('Markdown解析失败:', e);
            // 回退到基本的HTML转换
            return basicHtmlFormat(text);
        }
    } else {
        console.warn('Marked库未加载，使用基本格式化');
        return basicHtmlFormat(text);
    }
}

// 基本的HTML格式化（回退机制）
function basicHtmlFormat(text) {
    console.log('使用基本HTML格式化');
    
    if (!text || text.trim() === '') {
        return '';
    }
    
    // 基本的Markdown转换（无需转义，因为是markdown文本）
    let result = text
        // 代码块（三个反引号）
        .replace(/```([^`]*?)```/gs, '<pre><code>$1</code></pre>')
        // 行内代码
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // 标题
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
        // 粗体
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // 斜体
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // 链接
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // 无序列表
        .replace(/^\s*[-*+]\s+(.*)$/gm, '<li>$1</li>')
        // 有序列表
        .replace(/^\s*\d+\.\s+(.*)$/gm, '<li>$1</li>')
        // 换行符
        .replace(/\n\n+/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // 包装列表项
    result = result.replace(/(<li>.*?<\/li>(?:\s*<br>\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
    
    // 包装段落
    if (result && !result.startsWith('<')) {
        result = '<p>' + result + '</p>';
    }
    
    // 清理多余的换行
    result = result.replace(/<br>\s*<\/p>/g, '</p>')
                   .replace(/<p>\s*<br>/g, '<p>')
                   .replace(/<ul>\s*<br>/g, '<ul>')
                   .replace(/<\/li>\s*<br>/g, '</li>');
    
    console.log('基本格式化完成，输出长度:', result.length);
    return result;
}

// 获取知识库设置
function getKnowledgeSettings() {
    // 从本地存储获取设置，如果没有则使用默认值
    const savedSettings = localStorage.getItem('knowledgeSettings');
    let settings = {
        data_source: 'auto'  // 默认为自动
    };
    
    if (savedSettings) {
        try {
            const parsed = JSON.parse(savedSettings);
            settings = { ...settings, ...parsed };
        } catch (e) {
            console.error('解析存储的设置时出错:', e);
        }
    }
    
    // 如果页面上有数据源选择，则使用选择的值
    const dataSourceRadios = document.querySelectorAll('input[name="data-source"]');
    if (dataSourceRadios.length > 0) {
        for (const radio of dataSourceRadios) {
            if (radio.checked) {
                settings.data_source = radio.value;
                break;
            }
        }
    }
    
    return settings;
}

// 加载保存的知识库设置
function loadKnowledgeSettings() {
    const savedSettings = localStorage.getItem('knowledgeSettings');
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            
            // 应用表设置
            document.getElementById('outpatient').checked = settings.tables.outpatient;
            document.getElementById('target').checked = settings.tables.target;
            document.getElementById('drg').checked = settings.tables.drg;
            
            // 应用维度设置
            document.getElementById('department').checked = settings.dimensions.department;
            document.getElementById('specialty').checked = settings.dimensions.specialty;
            document.getElementById('target_completion').checked = settings.dimensions.target_completion;
            document.getElementById('trend').checked = settings.dimensions.trend;
            
            // 应用时间范围设置
            document.getElementById('allTime').checked = settings.timeRange === 'all';
            document.getElementById('lastMonth').checked = settings.timeRange === 'month';
            document.getElementById('lastWeek').checked = settings.timeRange === 'week';
        } catch (error) {
            console.error('解析知识库设置出错:', error);
        }
    }
}

/**
 * 导出聊天记录为PDF报告
 * @param {string} chatId - 聊天ID
 */
function exportChatReport(chatId) {
    // 检查是否提供了chatId
    if (!chatId) {
        showToast('错误: 无法导出报告，未提供聊天ID', 'error');
        return;
    }
    
    // 显示加载提示
    showToast('正在生成报告...', 'info');
    
    // 构建URL
    const url = `/chat/export_chat_report?chat_id=${chatId}&format=pdf`;
    
    // 打开新窗口下载报告
    window.open(url, '_blank');
}

// 显示提示消息
function showToast(message, type = 'info') {
    // 检查是否存在Utils全局对象
    if (window.Utils && Utils.dom && Utils.dom.showNotification) {
        Utils.dom.showNotification(message, type);
        return;
    }
    
    // 没有全局Utils对象时的简单替代方案
    const toast = document.createElement('div');
    toast.className = `chat-toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // 显示toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // 几秒后隐藏
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 向AI消息添加表格数据
function addTableToAIMessage(messageElement, tableData) {
    console.log('添加表格数据到AI消息:', tableData);
    
    if (!messageElement || !tableData) {
        console.error('无法添加表格：消息元素或表格数据为空');
        return;
    }
    
    try {
        const contentDiv = messageElement.querySelector('.chat-content .markdown-body');
        if (!contentDiv) {
            console.error('未找到Markdown内容区域');
            return;
        }
        
        // 为表格创建容器
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';
        
        // 添加表格标题
        if (tableData.title) {
            const titleElement = document.createElement('div');
            titleElement.className = 'table-title';
            titleElement.textContent = tableData.title;
            tableContainer.appendChild(titleElement);
        }
        
        // 创建表格元素
        const table = document.createElement('table');
        table.className = 'data-table';
        
        // 创建表头
        if (tableData.headers && tableData.headers.length > 0) {
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            tableData.headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
        }
        
        // 创建表格内容
        if (tableData.rows && tableData.rows.length > 0) {
            const tbody = document.createElement('tbody');
            
            tableData.rows.forEach(row => {
                const tr = document.createElement('tr');
                
                row.forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                
                tbody.appendChild(tr);
            });
            
            table.appendChild(tbody);
        }
        
        // 添加表格描述（如果有）
        if (tableData.description) {
            const descElement = document.createElement('div');
            descElement.className = 'table-description';
            descElement.textContent = tableData.description;
            tableContainer.appendChild(descElement);
        }
        
        // 将表格添加到容器
        tableContainer.appendChild(table);
        
        // 将表格容器添加到内容区域
        contentDiv.appendChild(tableContainer);
        
        console.log('表格已添加到消息中');
    } catch (error) {
        console.error('添加表格时出错:', error);
    }
}

// 处理AI响应中的表格数据
function processAIResponseTables(response, messageElement) {
    console.log('处理AI响应中的表格数据');
    
    // 检查是否有表格数据
    if (response && response.tables && Array.isArray(response.tables) && response.tables.length > 0) {
        console.log(`找到 ${response.tables.length} 个表格数据`);
        
        // 为每个表格创建HTML表格并添加到消息中
        response.tables.forEach(tableData => {
            addTableToAIMessage(messageElement, tableData);
        });
        
        return true;
    } else if (response && response.structured_result && response.structured_result.tables && 
              Array.isArray(response.structured_result.tables) && response.structured_result.tables.length > 0) {
        console.log(`在structured_result中找到 ${response.structured_result.tables.length} 个表格数据`);
        
        // 为每个表格创建HTML表格并添加到消息中
        response.structured_result.tables.forEach(tableData => {
            addTableToAIMessage(messageElement, tableData);
        });
        
        return true;
    }
    
    console.log('未找到表格数据');
    return false;
} 