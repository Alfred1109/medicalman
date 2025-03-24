document.addEventListener('DOMContentLoaded', function() {
    // 全局变量
    const chatInput = document.getElementById('message-input');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const toggleKnowledgePanel = document.getElementById('toggleKnowledgePanel');
    const knowledgePanel = document.getElementById('knowledgePanel');
    const historyButton = document.getElementById('historyButton');
    const clearChatButton = document.getElementById('clearChat');
    const exportReportButton = document.getElementById('exportReport');
    
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
    if (clearChatButton) {
        console.log('正在绑定清空聊天按钮点击事件');
        clearChatButton.onclick = function() {
            console.log('清空聊天按钮被点击');
            if (confirm('确定要清空所有聊天记录吗？')) {
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                    
                    // 添加初始欢迎消息
                    addAIMessage('您好，我是医院运营指标智能分析助手。请问有什么可以帮您解答的问题？');
                }
            }
        };
    } else {
        console.error('找不到清空聊天按钮元素');
    }
    
    // 导出报告按钮
    if (exportReportButton) {
        console.log('正在绑定导出报告按钮点击事件');
        exportReportButton.addEventListener('click', function() {
            console.log('导出报告按钮被点击');
            // 获取当前聊天的第一个问题作为标题
            let title = '智能问答记录';
            const firstUserMessage = document.querySelector('.chat-message.user .chat-bubble.user > div:first-child');
            if (firstUserMessage) {
                const question = firstUserMessage.textContent.trim();
                if (question.length > 0) {
                    title = `智能问答: ${question.substring(0, 30)}${question.length > 30 ? '...' : ''}`;
                }
            }
            
            // 调用导出函数
            exportChatReport(title);
        });
    } else {
        console.error('找不到导出报告按钮元素');
    }
    
    // 发送按钮点击事件
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // 输入框回车事件
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // 点击聊天建议
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('chat-suggestion')) {
            chatInput.value = e.target.textContent;
            sendMessage();
        }
    });
    
    // 页面加载时加载设置
    loadKnowledgeSettings();
}); 