// AI聊天API模块
// 处理与后端API的交互

// 全局变量
let currentConversationId = null;
let fileList = []; // 上传的文件列表

// 处理响应数据
function handleResponse(data, responseType) {
    console.log('开始处理响应数据:', data, '类型:', responseType);
    
    // 提取响应消息
    let responseMessage = '';
    
    // 根据不同情况提取消息内容
    if (data && typeof data === 'object') {
        // 检查是否有结构化分析结果（analysis、charts、tables等）
        if (data.analysis || (data.tables && data.tables.length > 0) || (data.summary && data.recommendations)) {
            console.log('检测到结构化分析数据，处理为格式化内容');
            
            // 构建格式化的Markdown响应
            let formattedResponse = '';
            
            // 添加分析内容
            if (data.analysis) {
                formattedResponse += `${data.analysis}\n\n`;
            }
            
            // 添加汇总部分
            if (data.summary) {
                formattedResponse += `## 分析摘要\n\n${data.summary}\n\n`;
            }
            
            // 添加建议部分
            if (data.recommendations) {
                formattedResponse += `## 建议\n\n${data.recommendations}\n\n`;
            }
            
            // 不添加表格和图表的描述，因为我们会单独处理它们
            
            responseMessage = formattedResponse;
        } else if (data.message) {
            responseMessage = data.message;
        } else if (data.text) {
            responseMessage = data.text;
        } else if (data.reply) {
            responseMessage = data.reply;
        } else if (data.response) {
            responseMessage = data.response;
        } else if (data.error) {
            responseMessage = `错误: ${data.error}`;
        } else {
            // 尝试检查是否有JSON格式的字符串
            if (typeof data.message === 'string' && (data.message.startsWith('{') || data.message.startsWith('['))) {
                try {
                    const jsonData = JSON.parse(data.message);
                    
                    // 如果解析成功且有结构化数据，则格式化显示
                    if (jsonData.analysis || jsonData.summary || jsonData.recommendations) {
                        let formattedResponse = '';
                        
                        // 添加分析内容
                        if (jsonData.analysis) {
                            formattedResponse += `${jsonData.analysis}\n\n`;
                        }
                        
                        // 添加汇总部分
                        if (jsonData.summary) {
                            formattedResponse += `## 分析摘要\n\n${jsonData.summary}\n\n`;
                        }
                        
                        // 添加建议部分
                        if (jsonData.recommendations) {
                            formattedResponse += `## 建议\n\n${jsonData.recommendations}\n\n`;
                        }
                        
                        responseMessage = formattedResponse;
                        
                        // 更新data对象，以便后续处理图表和表格
                        if (jsonData.charts) data.charts = jsonData.charts;
                        if (jsonData.tables) data.tables = jsonData.tables;
                    } else {
                        responseMessage = data.message;
                    }
                } catch (e) {
                    // 如果解析失败，则使用原始消息
                    responseMessage = data.message;
                }
            } else {
                // 尝试JSON序列化整个对象
                try {
                    responseMessage = "收到的数据: " + JSON.stringify(data, null, 2);
                } catch (e) {
                    responseMessage = "收到无法显示的数据";
                }
            }
        }
    } else if (typeof data === 'string') {
        // 尝试检查字符串是否是JSON格式
        if (data.startsWith('{') || data.startsWith('[')) {
            try {
                const jsonData = JSON.parse(data);
                
                // 如果解析成功且有结构化数据，则格式化显示
                if (jsonData.analysis || jsonData.summary || jsonData.recommendations) {
                    let formattedResponse = '';
                    
                    // 添加分析内容
                    if (jsonData.analysis) {
                        formattedResponse += `${jsonData.analysis}\n\n`;
                    }
                    
                    // 添加汇总部分
                    if (jsonData.summary) {
                        formattedResponse += `## 分析摘要\n\n${jsonData.summary}\n\n`;
                    }
                    
                    // 添加建议部分
                    if (jsonData.recommendations) {
                        formattedResponse += `## 建议\n\n${jsonData.recommendations}\n\n`;
                    }
                    
                    responseMessage = formattedResponse;
                    
                    // 更新data为解析后的对象，以便后续处理图表和表格
                    data = jsonData;
                } else {
                    responseMessage = data;
                }
            } catch (e) {
                // 如果解析失败，则使用原始字符串
                responseMessage = data;
            }
        } else {
            responseMessage = data;
        }
    } else {
        responseMessage = "收到未知响应";
    }
    
    console.log('提取的响应消息:', responseMessage);
    
    // 查找当前的"思考中"消息气泡
    const thinkingBubble = document.querySelector('.chat-bubble.ai.thinking');
    
    if (!thinkingBubble) {
        console.error('未找到正在思考的气泡，创建新的消息');
        // 如果没有找到思考气泡，创建一个新的消息
        const newMessageElement = addAIMessage(responseMessage);
        
        // 处理表格数据（如果有）
        if (newMessageElement) {
            processAIResponseTables(data, newMessageElement.closest('.chat-message'));
        }
        return;
    }
    
    console.log('找到思考气泡，更新内容');
    
    // 移除thinking类
    thinkingBubble.classList.remove('thinking');
    
    // 获取内容容器
    const contentDiv = thinkingBubble.querySelector('div:first-child');
    
    if (!contentDiv) {
        console.error('未找到内容容器，无法更新');
        return;
    }
    
    // 清空现有内容
    contentDiv.innerHTML = '';
    
    try {
        // 创建markdown容器
        const markdownDiv = document.createElement('div');
        markdownDiv.className = 'markdown-body';
        
        // 添加知识库引用标记 (如果存在)
        let kbReferenceHtml = '';
        if (data && data.type === 'knowledge_base' && data.reference_ids && data.reference_ids.length > 0) {
            console.log('添加知识库引用信息');
            kbReferenceHtml = `
                <div class="knowledge-reference">
                    <div class="reference-icon"><i class="fas fa-book"></i></div>
                    <div class="reference-text">回答基于知识库内容</div>
                </div>
            `;
        }
        
        // 尝试解析Markdown内容
        try {
            console.log('将要渲染的Markdown内容:', responseMessage);
            const parsedContent = parseMarkdown(responseMessage);
            console.log('解析后的HTML内容:', parsedContent);
            
            // 添加知识库引用标记和Markdown内容
            contentDiv.innerHTML = `
                ${kbReferenceHtml}
                <div class="markdown-body">${parsedContent}</div>
            `;
            console.log('HTML内容已设置到DOM');
        } catch (error) {
            console.error('渲染Markdown时出错:', error);
            contentDiv.innerHTML = `
                ${kbReferenceHtml}
                <div class="markdown-body">${responseMessage}</div>
            `;
        }
        
        // 应用代码高亮
        try {
            const codeBlocks = contentDiv.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                hljs.highlightBlock(block);
            });
        } catch (e) {
            console.error('代码高亮错误:', e);
        }
        
        // 更新时间戳
        const timeDiv = thinkingBubble.querySelector('.chat-time');
        if (timeDiv) {
            timeDiv.textContent = getCurrentTime();
        }
        
        console.log('AI消息内容已更新');
        
        // 处理表格数据（如果有）
        const messageElement = thinkingBubble.closest('.chat-message');
        if (messageElement) {
            processAIResponseTables(data, messageElement);
        }
        
        // 处理图表数据
        if (data && data.charts && Array.isArray(data.charts) && data.charts.length > 0) {
            console.log(`处理${data.charts.length}个图表`);
            console.log('图表数据详情:', JSON.stringify(data.charts));
            
            // 添加图表容器
            const chartsContainer = document.createElement('div');
            chartsContainer.className = 'charts-container';
            contentDiv.appendChild(chartsContainer);
            
            // 延迟初始化图表，确保DOM已经更新
            setTimeout(() => {
                data.charts.forEach((chartConfig, index) => {
                    console.log(`处理图表 ${index+1}:`, chartConfig);
                    
                    // 创建图表容器
                    const chartDiv = document.createElement('div');
                    chartDiv.className = 'analysis-chart';
                    chartsContainer.appendChild(chartDiv);
                    
                    // 添加图表标题和操作按钮
                    let titleText = '';
                    if (typeof chartConfig.title === 'string') {
                        titleText = chartConfig.title;
                    } else if (chartConfig.title && chartConfig.title.text) {
                        titleText = chartConfig.title.text;
                    } else {
                        titleText = `图表 ${index+1}`;
                    }
                    
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'chart-header';
                    chartDiv.appendChild(headerDiv);
                    
                    const titleElem = document.createElement('h3');
                    titleElem.className = 'chart-title';
                    titleElem.textContent = titleText;
                    headerDiv.appendChild(titleElem);
                    
                    // 添加操作按钮区域
                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'chart-actions';
                    headerDiv.appendChild(actionsDiv);
                    
                    // 下载按钮
                    const downloadBtn = document.createElement('div');
                    downloadBtn.className = 'chart-action';
                    downloadBtn.title = '下载';
                    downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                    actionsDiv.appendChild(downloadBtn);
                    
                    // 全屏按钮
                    const fullscreenBtn = document.createElement('div');
                    fullscreenBtn.className = 'chart-action';
                    fullscreenBtn.title = '全屏';
                    fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
                    actionsDiv.appendChild(fullscreenBtn);
                    
                    // 创建图表容器
                    const chartContainer = document.createElement('div');
                    chartContainer.className = 'chart-container';
                    chartContainer.id = `chat-chart-${Date.now()}-${index}`;
                    chartDiv.appendChild(chartContainer);
                    
                    // 使用新的图表工具初始化echarts
                    try {
                        console.log(`初始化图表 ${index+1}`);
                        
                        // 处理直接使用config属性的情况
                        let finalConfig;
                        if (chartConfig.config) {
                            console.log('使用chartConfig.config作为图表配置');
                            // 适配Chart.js格式到ECharts格式
                            finalConfig = Utils.chart.convertChartJsToECharts(chartConfig.config);
                        } else {
                            // 确保图表配置符合echarts要求
                            finalConfig = {...chartConfig};
                            
                            // 处理标题格式
                            if (typeof finalConfig.title === 'string') {
                                finalConfig.title = {
                                    text: finalConfig.title
                                };
                            }
                        }
                        
                        console.log('最终图表配置:', JSON.stringify(finalConfig));
                        
                        // 使用统一的图表工具初始化
                        const chart = Utils.chart.initChart(chartContainer.id, finalConfig);
                        
                        // 设置按钮事件
                        if (chart) {
                            downloadBtn.addEventListener('click', () => {
                                Utils.chart.downloadChart(chart, `ai-chat-chart-${index+1}`);
                            });
                            
                            fullscreenBtn.addEventListener('click', () => {
                                Utils.chart.fullscreenChart(chart);
                            });
                        }
                        
                        console.log(`图表 ${index+1} 渲染成功`);
                    } catch (e) {
                        console.error(`图表渲染错误:`, e);
                        console.error('错误的图表配置:', JSON.stringify(chartConfig));
                        chartContainer.innerHTML = `<div class="chart-error-message">图表渲染失败: ${e.message}</div>`;
                    }
                });
            }, 100);
        } else {
            console.log('没有图表数据需要渲染');
            console.log('data对象包含以下字段:', Object.keys(data || {}));
            if (data) {
                console.log('data.charts是否存在:', 'charts' in data);
                console.log('data.charts的类型:', data.charts ? typeof data.charts : 'undefined');
                console.log('data.charts的值:', data.charts);
            }
        }
        
    } catch (error) {
        console.error('处理响应时发生错误:', error);
        contentDiv.textContent = '处理响应时出错，请重试';
    }
    
    // 确保滚动到底部
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * 获取CSRF令牌
 * @returns {string} CSRF令牌
 */
function getCsrfToken() {
    let csrfToken = '';
    
    // 从meta标签获取
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    if (tokenElement && tokenElement.content) {
        csrfToken = tokenElement.content;
    } else {
        // 从cookie获取
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrf_token=')) {
                csrfToken = cookie.substring('csrf_token='.length);
                break;
            }
        }
    }
    
    if (!csrfToken) {
        console.warn('未找到CSRF令牌，请求可能会被拒绝');
    }
    
    return csrfToken;
}

// 发送消息
function sendMessage(message, callback) {
    if (!message || message.trim() === '') {
        console.error('消息不能为空');
        return;
    }

    // 获取CSRF令牌
    const csrfToken = getCsrfToken();
    
    // 尝试获取知识库设置
    let knowledgeSettings = {};
    if (typeof window.getKnowledgeSettings === 'function') {
        try {
            knowledgeSettings = window.getKnowledgeSettings();
            console.log('应用知识库设置:', knowledgeSettings);
        } catch (error) {
            console.warn('获取知识库设置失败:', error);
        }
    } else {
        console.log('getKnowledgeSettings未定义，使用默认设置');
    }

    // 构建请求数据
    const requestData = {
        message: message,
        attachments: fileList.length > 0 ? fileList.map(file => file.path || file.name) : [],
        knowledge_settings: knowledgeSettings
    };

    // 发送请求
    fetch('/chat/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (typeof callback === 'function') {
            callback(null, data);
        }
    })
    .catch(error => {
        console.error('发送消息时出错:', error);
        if (typeof callback === 'function') {
            callback(error, null);
        }
    });
}

// 处理文件上传
function handleFiles(files) {
    const uploadedFiles = document.getElementById('uploadedFiles');
    if (!files || files.length === 0) return;
    
    Array.from(files).forEach(file => {
        // 检查文件类型
        const allowedTypes = ['.pdf', '.docx', '.txt', '.xlsx', '.xls', '.csv'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExt)) {
            alert('不支持的文件格式！仅支持PDF、DOCX、TXT、XLSX、XLS和CSV文件。');
            return;
        }
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('document', file);
        
        // 显示上传中状态
        const tempFileItem = document.createElement('div');
        tempFileItem.className = 'file-item';
        tempFileItem.innerHTML = `
            <span class="file-name">${file.name} (上传中...)</span>
        `;
        uploadedFiles.appendChild(tempFileItem);
        
        // 发送文件到服务器
        fetch('/api/ai-chat/upload-document', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 移除临时项
            tempFileItem.remove();
            
            if (data.success) {
                // 添加文件到列表
                addFileToList(file.name, data.filename);
            } else {
                alert('上传失败：' + (data.error || data.message || '未知错误'));
            }
        })
        .catch(error => {
            // 移除临时项
            tempFileItem.remove();
            console.error('Error:', error);
            alert('上传出错，请重试');
        });
    });
}

// 添加文件到显示列表
function addFileToList(fileName, fileId) {
    const uploadedFiles = document.getElementById('uploadedFiles');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <span class="file-name">${fileName}</span>
        <span class="file-remove" data-file-id="${fileId}">
            <i class="fas fa-times"></i>
        </span>
    `;
    
    // 添加删除功能
    const removeBtn = fileItem.querySelector('.file-remove');
    removeBtn.addEventListener('click', () => {
        fetch('/api/ai-chat/delete-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({filename: fileId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fileItem.remove();
            } else {
                alert('删除失败：' + (data.error || data.message || '未知错误'));
            }
        });
    });
    
    uploadedFiles.appendChild(fileItem);
}

// 将Chart.js格式转换为ECharts格式
function adaptChartJsToECharts(chartJsConfig) {
    return Utils.chart.convertChartJsToECharts(chartJsConfig);
}

// 暴露API到全局作用域
window.ChatAPI = {
    sendMessage: sendMessage,
    handleFiles: function(files) {
        if (typeof FileUpload !== 'undefined' && FileUpload.handleFiles) {
            return FileUpload.handleFiles(files);
        } else {
            console.error('FileUpload模块未加载或handleFiles方法未定义');
            return false;
        }
    },
    getCsrfToken: getCsrfToken,
    setCurrentConversationId: function(id) {
        currentConversationId = id;
        console.log('设置会话ID:', id);
    },
    getCurrentConversationId: function() {
        return currentConversationId;
    },
    getFileList: function() {
        return fileList;
    },
    addToFileList: function(file) {
        fileList.push(file);
    },
    clearFileList: function() {
        fileList = [];
    },
    removeFileFromList: function(filename) {
        fileList = fileList.filter(file => 
            (file.name !== filename && (!file.path || file.path !== filename))
        );
    }
};

// 当DOM内容加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI聊天API模块已加载');
    
    // 检查FileUpload是否可用
    setTimeout(() => {
        if (typeof FileUpload === 'undefined') {
            console.warn('FileUpload模块未加载，文件上传功能可能不可用');
        } else {
            console.log('FileUpload模块已加载');
        }
        
        if (typeof getKnowledgeSettings === 'undefined') {
            console.warn('getKnowledgeSettings函数未定义，将使用默认知识库设置');
        } else {
            console.log('getKnowledgeSettings函数已定义');
        }
    }, 500);
}); 