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

    // 显示加载指示器 - 使用条状思考动画替代旋转动画
    addMessage('assistant', '<div class="thinking-message">思考中<span class="typing-indicator"><span></span><span></span><span></span></span></div>', 'loading-message');

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

// 页面初始化
$(document).ready(function() {
    // 页面加载完成后隐藏加载动画
    $('#page-loader').fadeOut();
    
    // 初始化主题
    initTheme();
    
    // 主题切换
    $('.theme-option').click(function(e) {
        e.preventDefault();
        const theme = $(this).data('theme');
        setTheme(theme);
    });
    
    // 移动端侧边栏处理
    const sidebarMenu = document.getElementById('sidebarMenu');
    if (sidebarMenu) {
        // 在小屏幕上点击菜单项后自动关闭侧边栏
        const menuLinks = sidebarMenu.querySelectorAll('.list-group-item-action');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    const bsOffcanvas = bootstrap.Offcanvas.getInstance(sidebarMenu);
                    if (bsOffcanvas) {
                        bsOffcanvas.hide();
                    }
                }
            });
        });
    }
});

// 立即执行清除重复标题
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixDuplicateTitles);
    } else {
        fixDuplicateTitles();
    }
    
    function fixDuplicateTitles() {
        setTimeout(() => {
            // 查找所有图表标题
            const titles = document.querySelectorAll('.chart-title');
            const titlesByText = {};
            
            // 收集每个文本内容对应的标题元素
            titles.forEach(title => {
                const text = title.textContent.trim();
                if (!titlesByText[text]) {
                    titlesByText[text] = [];
                }
                titlesByText[text].push(title);
            });
            
            // 对于每组相同文本的标题，保留第一个，删除其余的
            Object.values(titlesByText).forEach(titleGroup => {
                if (titleGroup.length > 1) {
                    // 保留第一个，删除其余的
                    for (let i = 1; i < titleGroup.length; i++) {
                        const title = titleGroup[i];
                        // 如果标题是chart-header的子元素，可能需要移除整个header
                        const header = title.closest('.chart-header');
                        if (header) {
                            header.remove();
                        } else {
                            title.remove();
                        }
                    }
                }
            });
            
            console.log('重复标题清理完成');
        }, 500); // 等待500毫秒以确保DOM已完全加载
    }
})();

// 等待文档加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化移动端菜单
    initMobileMenu();
    
    // 初始化页面加载器
    initPageLoader();
    
    // 初始化通知功能
    initNotifications();
    
    // 清除重复标题
    cleanupDuplicateChartTitles();
    
    // 初始增强
    enhanceChartContainers();
    
    // 监听DOM变化，找到新添加的图表容器并增强
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                cleanupDuplicateChartTitles();
                enhanceChartContainers();
            }
        });
    });
    
    // 开始观察文档变化
    observer.observe(document.body, { childList: true, subtree: true });
});

// 初始化移动端菜单
function initMobileMenu() {
    const menuToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.getElementById('sidebarMenu');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // 点击内容区域时关闭菜单
        document.querySelector('.content-wrapper').addEventListener('click', function() {
            if (window.innerWidth < 992 && sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
        
        // 监听窗口大小变化
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 992) {
                sidebar.classList.remove('show');
            }
        });
    }
}

// 初始化页面加载器
function initPageLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        window.addEventListener('load', function() {
            loader.style.display = 'none';
        });
    }
}

// 初始化通知功能
function initNotifications() {
    // 获取未读通知数量
    getUnreadNotificationsCount();
}

// 获取未读通知数量
function getUnreadNotificationsCount() {
    /*
    // 暂时禁用通知数量获取，避免404错误
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const notificationBadge = document.querySelector('.notification-badge');
            
            if (notificationBadge) {
                if (data.count > 0) {
                    notificationBadge.textContent = data.count > 99 ? '99+' : data.count;
                    notificationBadge.style.display = 'flex';
                } else {
                    notificationBadge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('获取通知数量失败:', error));
    */
    
    // 通知功能暂未实现，隐藏通知徽章
    const notificationBadge = document.querySelector('.notification-badge');
    if (notificationBadge) {
        notificationBadge.style.display = 'none';
    }
}

// 标记通知为已读
function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/mark-read`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新通知UI
                getUnreadNotificationsCount();
            }
        })
        .catch(error => console.error('标记通知失败:', error));
}

// 导出函数
window.markNotificationAsRead = markNotificationAsRead;
window.cleanupDuplicateChartTitles = cleanupDuplicateChartTitles;

// 增强所有图表容器，添加下载和全屏按钮
function enhanceChartContainers() {
    document.querySelectorAll('.chart-container').forEach(container => {
        // 跳过已经增强过的容器
        if (container.getAttribute('data-enhanced') === 'true') return;
        
        // 获取父元素，通常是card-body或类似的容器
        const parent = container.parentElement;
        if (!parent) return;
        
        // 检查是否已经有chart-header元素
        const existingHeader = parent.querySelector('.chart-header');
        if (existingHeader) {
            // 已有标题，只需添加操作按钮
            const actionsDiv = existingHeader.querySelector('.chart-actions');
            if (!actionsDiv) {
                // 如果没有操作区，创建一个
                const newActionsDiv = document.createElement('div');
                newActionsDiv.className = 'chart-actions';
                
                // 下载按钮
                const downloadBtn = document.createElement('div');
                downloadBtn.className = 'chart-action';
                downloadBtn.title = '下载';
                downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                
                // 全屏按钮
                const fullscreenBtn = document.createElement('div');
                fullscreenBtn.className = 'chart-action';
                fullscreenBtn.title = '全屏';
                fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
                
                // 添加按钮到操作区
                newActionsDiv.appendChild(downloadBtn);
                newActionsDiv.appendChild(fullscreenBtn);
                
                // 添加操作区到标题栏
                existingHeader.appendChild(newActionsDiv);
                
                // 查找是否有echarts实例关联到此容器
                const chart = window.echartsInstances ? 
                    window.echartsInstances.find(c => c && c.getDom && c.getDom() === container) : null;
                
                // 如果找到图表实例，设置按钮事件
                if (chart) {
                    downloadBtn.addEventListener('click', () => {
                        Utils.chart.downloadChart(chart, container.id || 'chart');
                    });
                    
                    fullscreenBtn.addEventListener('click', () => {
                        Utils.chart.fullscreenChart(chart);
                    });
                } else {
                    // 如果没有找到图表实例，禁用按钮
                    downloadBtn.classList.add('disabled');
                    fullscreenBtn.classList.add('disabled');
                }
            }
            
            // 标记为已增强
            container.setAttribute('data-enhanced', 'true');
            return;
        }
        
        // 查找父元素中是否已有标题元素
        const existingTitle = parent.querySelector('.chart-title, .card-title, h3, h4');
        let titleText = existingTitle ? existingTitle.textContent.trim() : '图表';
        
        // 如果父元素是card-body，标题可能在card-header中
        if (parent.classList.contains('card-body')) {
            const cardElement = parent.parentElement;
            if (cardElement && cardElement.classList.contains('card')) {
                const cardHeader = cardElement.querySelector('.card-header');
                if (cardHeader) {
                    titleText = cardHeader.textContent.trim();
                }
            }
        }
        
        // 创建标题和操作区
        const headerDiv = document.createElement('div');
        headerDiv.className = 'chart-header';
        
        const titleDiv = document.createElement('h3');
        titleDiv.className = 'chart-title';
        titleDiv.textContent = titleText;
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'chart-actions';
        
        // 下载按钮
        const downloadBtn = document.createElement('div');
        downloadBtn.className = 'chart-action';
        downloadBtn.title = '下载';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
        
        // 全屏按钮
        const fullscreenBtn = document.createElement('div');
        fullscreenBtn.className = 'chart-action';
        fullscreenBtn.title = '全屏';
        fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        
        // 组装UI元素
        actionsDiv.appendChild(downloadBtn);
        actionsDiv.appendChild(fullscreenBtn);
        headerDiv.appendChild(titleDiv);
        headerDiv.appendChild(actionsDiv);
        
        // 查找是否有echarts实例关联到此容器
        const chart = window.echartsInstances ? 
            window.echartsInstances.find(c => c && c.getDom && c.getDom() === container) : null;
        
        // 如果找到图表实例，设置按钮事件
        if (chart) {
            downloadBtn.addEventListener('click', () => {
                Utils.chart.downloadChart(chart, container.id || 'chart');
            });
            
            fullscreenBtn.addEventListener('click', () => {
                Utils.chart.fullscreenChart(chart);
            });
        } else {
            // 如果没有找到图表实例，禁用按钮
            downloadBtn.classList.add('disabled');
            fullscreenBtn.classList.add('disabled');
        }
        
        // 如果发现页面上已经有相同的标题，就不再添加
        const similarTitles = Array.from(document.querySelectorAll('.chart-title, .card-title, h3, h4'))
            .filter(el => el.textContent.trim() === titleText && el !== titleDiv);
        
        if (similarTitles.length === 0) {
            // 将现有容器替换为新结构
            // 只有在容器不是作为card-body的直接子元素时才进行DOM修改
            if (!parent.classList.contains('card-body')) {
                container.parentNode.insertBefore(headerDiv, container);
            }
        }
        
        // 标记为已增强
        container.setAttribute('data-enhanced', 'true');
    });
}

// 清除重复的图表标题
function cleanupDuplicateChartTitles() {
    // 查找所有图表标题
    const titles = document.querySelectorAll('.chart-title');
    const titlesByText = {};
    
    // 收集每个文本内容对应的标题元素
    titles.forEach(title => {
        const text = title.textContent.trim();
        if (!titlesByText[text]) {
            titlesByText[text] = [];
        }
        titlesByText[text].push(title);
    });
    
    // 对于每组相同文本的标题，保留第一个，删除其余的
    Object.values(titlesByText).forEach(titleGroup => {
        if (titleGroup.length > 1) {
            // 保留第一个，删除其余的
            for (let i = 1; i < titleGroup.length; i++) {
                const title = titleGroup[i];
                // 如果标题是chart-header的子元素，可能需要移除整个header
                const header = title.closest('.chart-header');
                if (header) {
                    header.remove();
                } else {
                    title.remove();
                }
            }
        }
    });
}

// 立即执行的重复标题清理（确保页面渲染后立即处理）
(function() {
    setTimeout(function() {
        if (typeof cleanupDuplicateChartTitles === 'function') {
            cleanupDuplicateChartTitles();
            console.log('初始标题重复清理已执行');
        }
    }, 100);
})(); 