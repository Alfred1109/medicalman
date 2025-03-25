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
                    console.log(`图表类型: ${chartConfig.type || '未指定'}`);
                    console.log(`是否有xAxis: ${'xAxis' in chartConfig}`);
                    console.log(`是否有series: ${'series' in chartConfig}`);
                    
                    // 创建图表容器
                    const chartDiv = document.createElement('div');
                    chartDiv.className = 'chart-item';
                    chartDiv.id = `chart-${Date.now()}-${index}`;
                    chartDiv.style.width = '100%';
                    chartDiv.style.height = '350px';
                    chartsContainer.appendChild(chartDiv);
                    
                    // 添加图表标题
                    let titleText = '';
                    if (typeof chartConfig.title === 'string') {
                        titleText = chartConfig.title;
                    } else if (chartConfig.title && chartConfig.title.text) {
                        titleText = chartConfig.title.text;
                    } else {
                        titleText = `图表 ${index+1}`;
                    }
                    
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'chart-title';
                    titleDiv.textContent = titleText;
                    chartDiv.appendChild(titleDiv);
                    
                    // 创建图表画布
                    const chartCanvas = document.createElement('div');
                    chartCanvas.style.width = '100%';
                    chartCanvas.style.height = '300px';
                    chartDiv.appendChild(chartCanvas);
                    
                    // 初始化echarts
                    try {
                        console.log(`初始化图表 ${index+1}`);
                        const chart = echarts.init(chartCanvas);
                        
                        // 处理直接使用config属性的情况
                        if (chartConfig.config) {
                            console.log('使用chartConfig.config作为图表配置');
                            // 适配Chart.js格式到ECharts格式
                            const adaptedConfig = adaptChartJsToECharts(chartConfig.config);
                            chart.setOption(adaptedConfig);
                        } else {
                            // 确保图表配置符合echarts要求
                            let finalConfig = {...chartConfig};
                            
                            // 处理标题格式
                            if (typeof finalConfig.title === 'string') {
                                finalConfig.title = {
                                    text: finalConfig.title,
                                    left: 'center'
                                };
                            }
                            
                            // 设置图表配置
                            console.log('最终图表配置:', JSON.stringify(finalConfig));
                            chart.setOption(finalConfig);
                        }
                        
                        // 适应窗口大小变化
                        window.addEventListener('resize', () => {
                            chart.resize();
                        });
                        
                        console.log(`图表 ${index+1} 渲染成功`);
                    } catch (e) {
                        console.error(`图表渲染错误:`, e);
                        console.error('错误的图表配置:', JSON.stringify(chartConfig));
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'chart-error';
                        errorDiv.textContent = `图表渲染失败: ${e.message}`;
                        chartDiv.appendChild(errorDiv);
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

// 发送消息
function sendMessage() {
    const chatInput = document.getElementById('message-input');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // 清空输入框
    chatInput.value = '';
    
    // 添加用户消息到聊天界面
    addUserMessage(message);
    
    // 添加AI消息（加载状态）
    const aiMsgElement = addAIMessage('思考中', true);
    console.log('已添加思考中消息元素:', aiMsgElement);
    
    // 获取知识库设置
    const knowledgeSettings = getKnowledgeSettings();
    
    console.log('发送消息:', message);
    console.log('知识库设置:', knowledgeSettings);
    
    // 发送请求到后端
    fetch('/chat/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: message,
            knowledge_settings: knowledgeSettings
        })
    })
    .then(response => {
        console.log('收到响应:', response);
        
        // 检查响应状态
        if (!response.ok) {
            console.error(`API响应状态错误: ${response.status} ${response.statusText}`);
            throw new Error(`服务器响应错误: ${response.status}`);
        }
        
        // 以文本形式获取响应，然后手动解析
        return response.text().then(text => {
            try {
                // 处理NaN、Infinity等特殊值
                const cleanedText = text.replace(/:\s*NaN\b/g, ': "NaN"')
                                       .replace(/:\s*Infinity\b/g, ': "Infinity"')
                                       .replace(/:\s*-Infinity\b/g, ': "-Infinity"')
                                       .replace(/:\s*undefined\b/g, ': null');
                
                // 尝试解析清理后的JSON
                return JSON.parse(cleanedText);
            } catch (e) {
                console.error('JSON解析错误:', e, '原始文本:', text);
                // 返回一个错误对象而不是抛出异常，这样可以在后续处理
                return {
                    success: false,
                    message: `JSON解析错误: ${e.message}`,
                    originalText: text.substring(0, 500) // 限制长度以避免过大的日志
                };
            }
        });
    })
    .then(data => {
        console.log('解析的JSON数据:', data);
        console.log('数据类型:', typeof data);
        console.log('是否有success字段:', 'success' in data);
        console.log('是否有message字段:', 'message' in data);
        console.log('是否有type字段:', 'type' in data);
        console.log('是否有data字段:', 'data' in data);
        
        // 检查响应是否成功
        if (data && data.success) {
            console.log('API响应成功');
            
            // 确保响应中有message字段
            const responseMessage = data.message || "未收到有效回复";
            console.log('响应消息:', responseMessage);
            
            // 确定响应类型
            const responseType = data.type || "text";
            console.log('响应类型:', responseType);
            
            // 根据响应类型处理结果
            if (responseType === 'data_analysis' || responseType === 'data_only') {
                console.log('处理数据分析响应');
                // 数据分析结果，包含图表数据
                const resultObj = {
                    text: responseMessage,
                    data: data.data || []
                };
                
                // 如果有图表数据，添加到结果对象
                if (data.charts) {
                    console.log(`添加${data.charts.length}个图表到结果对象`);
                    resultObj.charts = data.charts;
                }
                
                handleResponse(resultObj, responseType);
            } 
            else if (responseType === 'excel_analysis' || responseType === 'file_analysis') {
                console.log('处理文件分析响应');
                // 文件分析结果
                handleResponse(data, responseType);
            }
            else {
                console.log('处理普通文本响应');
                // 普通文本响应
                handleResponse(data, responseType);
            }
        } else {
            console.error('API响应失败或格式错误');
            // 显示错误消息
            const errorMessage = data && data.message ? data.message : 
                               (data && data.error ? data.error : "处理请求时出错");
            console.log('显示错误消息:', errorMessage);
            handleResponse({success: false, message: errorMessage}, 'error');
        }
    })
    .catch(error => {
        console.error('请求出错:', error);
        handleResponse({success: false, message: `请求错误: ${error.message}`}, 'error');
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
    const config = chartJsConfig || {};
    const chartType = config.type || 'bar';
    const datasets = (config.data && config.data.datasets) || [];
    const labels = (config.data && config.data.labels) || [];
    
    // 创建ECharts配置
    const echartsConfig = {
        title: {
            text: config.options && config.options.plugins && config.options.plugins.title 
                ? config.options.plugins.title.text : '数据图表',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: datasets.map(ds => ds.label || '数据'),
            top: '8%'
        },
        xAxis: {
            type: 'category',
            data: labels
        },
        yAxis: {
            type: 'value'
        },
        series: datasets.map(ds => {
            return {
                name: ds.label || '数据',
                type: ds.type || chartType,
                data: ds.data,
                itemStyle: {
                    color: ds.backgroundColor || '#5470c6'
                }
            }
        })
    };
    
    console.log('转换后的ECharts配置:', echartsConfig);
    return echartsConfig;
} 