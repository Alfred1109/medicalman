// 添加消息到聊天界面
function addMessage(sender, message, className = '') {
    const messageDiv = $('<div>').addClass('message ' + sender + ' ' + className);
    messageDiv.html(message);
    $('#chat-messages').append(messageDiv);
    scrollToBottom();
}

// 滚动到底部
function scrollToBottom() {
    const chatContainer = $('#chat-messages');
    chatContainer.scrollTop(chatContainer[0].scrollHeight);
}

// 显示图表
function displayCharts(charts) {
    if (!charts || charts.length === 0) return;
    
    // 创建图表容器
    const chartsContainer = $('<div>').addClass('charts-container');
    $('#chat-messages').append(chartsContainer);
    
    // 为每个图表创建一个div
    charts.forEach((chart, index) => {
        const chartDiv = $('<div>')
            .addClass('chart-item')
            .attr('id', 'chart-' + index)
            .css({
                'width': '100%',
                'height': '300px',
                'margin-bottom': '20px'
            });
        
        chartsContainer.append(chartDiv);
        
        // 初始化ECharts实例
        const chartInstance = echarts.init(document.getElementById('chart-' + index));
        
        // 设置图表选项
        chartInstance.setOption(chart);
        
        // 响应窗口大小变化
        $(window).on('resize', function() {
            chartInstance.resize();
        });
    });
    
    scrollToBottom();
}

// 发送用户查询
function sendQuery() {
    const userMessage = $('#user-input').val().trim();
    if (!userMessage) return;

    // 清空输入框
    $('#user-input').val('');

    // 添加用户消息到聊天界面
    addMessage('user', userMessage);

    // 显示加载指示器
    addMessage('assistant', '<div class="loading-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', 'loading-message');

    // 发送请求到后端
    $.ajax({
        url: '/api/query',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            message: userMessage,
            data_source: currentDataSource
        }),
        success: function(response) {
            // 移除加载消息
            $('.loading-message').remove();

            if (response.success) {
                // 根据响应类型处理结果
                if (response.type === 'excel_analysis') {
                    // 显示Excel分析结果
                    const message = `<div class="file-analysis">
                        <div class="file-info">
                            <i class="fas fa-file-excel"></i>
                            <span>${response.file_name}</span>
                        </div>
                        <div class="analysis-content">${marked.parse(response.message)}</div>
                    </div>`;
                    
                    // 如果有图表，添加图表
                    if (response.charts && response.charts.length > 0) {
                        addMessage('assistant', message);
                        displayCharts(response.charts);
                    } else {
                        addMessage('assistant', message);
                    }
                } 
                else if (response.type === 'text_analysis') {
                    // 显示文本分析结果
                    const fileIcon = getFileIcon(response.file_name);
                    const message = `<div class="file-analysis">
                        <div class="file-info">
                            <i class="${fileIcon}"></i>
                            <span>${response.file_name}</span>
                        </div>
                        <div class="analysis-content">${marked.parse(response.message)}</div>
                    </div>`;
                    addMessage('assistant', message);
                }
                else if (response.type === 'knowledge_base') {
                    // 显示知识库查询结果
                    let message = marked.parse(response.message);
                    
                    // 如果有来源，添加来源信息
                    if (response.sources && response.sources.length > 0) {
                        message += '<div class="sources-section"><h4>参考来源：</h4><ul>';
                        response.sources.forEach(source => {
                            message += `<li>${source}</li>`;
                        });
                        message += '</ul></div>';
                    }
                    
                    addMessage('assistant', message);
                }
                else {
                    // 显示一般回复
                    addMessage('assistant', marked.parse(response.message));
                }
            } else {
                // 显示错误消息
                addMessage('assistant', `<div class="error-message">${response.message}</div>`);
            }
            
            // 滚动到底部
            scrollToBottom();
        },
        error: function(xhr, status, error) {
            // 移除加载消息
            $('.loading-message').remove();
            
            // 显示错误消息
            addMessage('assistant', `<div class="error-message">请求失败: ${error}</div>`);
            
            // 滚动到底部
            scrollToBottom();
        }
    });
}

// 根据文件名获取适当的图标
function getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'pdf':
            return 'fas fa-file-pdf';
        case 'docx':
        case 'doc':
            return 'fas fa-file-word';
        case 'txt':
            return 'fas fa-file-alt';
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif':
            return 'fas fa-file-image';
        default:
            return 'fas fa-file';
    }
} 