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
    // 检查marked库是否可用
    if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
        try {
            return marked.parse(text);
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
    // 安全地转义HTML特殊字符
    const escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // 基本的Markdown转换
    return escaped
        // 粗体
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // 斜体
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // 换行
        .replace(/\n/g, '<br>')
        // 标题
        .replace(/#{1,6}\s+(.*?)(?:\n|$)/g, function(match, content) {
            const level = match.trim().indexOf(' ');
            return `<h${level}>${content}</h${level}>`;
        })
        // 列表项
        .replace(/^\s*\-\s+(.*?)(?:\n|$)/mg, '<li>$1</li>')
        // 包装列表项
        .replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
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

// 导出聊天记录为PDF报告
function exportChatReport(title) {
    console.log('准备导出聊天记录');
    
    // 获取所有聊天消息
    const chatMessages = document.querySelectorAll('.chat-message');
    if (!chatMessages || chatMessages.length === 0) {
        console.error('没有可导出的聊天内容');
        showToast('没有可导出的聊天内容', 'error');
        return;
    }
    
    // 构建聊天历史数据
    const chatHistory = [];
    chatMessages.forEach(messageElem => {
        // 确定消息类型
        const isAI = messageElem.querySelector('.chat-avatar.ai') !== null;
        const role = isAI ? 'ai' : 'user';
        
        // 获取消息内容
        let content = '';
        const contentElem = messageElem.querySelector('.chat-bubble > div:first-child');
        if (contentElem) {
            // 如果是AI消息，可能包含markdown或图表
            if (isAI) {
                const markdownElem = contentElem.querySelector('.markdown-body');
                if (markdownElem) {
                    content = markdownElem.innerHTML;
                } else {
                    content = contentElem.innerHTML;
                }
            } else {
                content = contentElem.textContent;
            }
        }
        
        // 获取时间
        let time = '';
        const timeElem = messageElem.querySelector('.chat-time');
        if (timeElem) {
            time = timeElem.textContent;
        }
        
        // 获取图表信息
        const charts = [];
        const chartElems = messageElem.querySelectorAll('.chart-container');
        chartElems.forEach(chartElem => {
            const titleElem = chartElem.querySelector('.chart-title');
            const title = titleElem ? titleElem.textContent : '图表';
            
            // 目前无法导出图表图像，只记录图表标题
            charts.push({
                title: title
            });
        });
        
        // 添加到聊天历史
        chatHistory.push({
            role: role,
            content: content,
            content_type: isAI ? 'markdown' : 'text',
            time: time,
            charts: charts.length > 0 ? charts : null
        });
    });
    
    // 默认标题
    if (!title) {
        title = '智能问答记录 - ' + new Date().toLocaleDateString();
    }
    
    // 显示加载提示
    showToast('正在生成报告，请稍候...', 'info');
    
    // 请求生成报告
    fetch('/chat/export-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chat_history: chatHistory,
            title: title
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`服务器响应错误: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        // 创建下载链接
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `chat_report_${new Date().getTime()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        showToast('报告生成成功', 'success');
    })
    .catch(error => {
        console.error('导出报告失败:', error);
        showToast('导出报告失败: ' + error.message, 'error');
    });
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