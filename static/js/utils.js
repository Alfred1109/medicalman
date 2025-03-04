// 数据缓存管理
const CacheManager = {
    set: function(key, data, expiration = 3600000) { // 默认1小时过期
        const item = {
            data: data,
            timestamp: new Date().getTime(),
            expiration: expiration
        };
        localStorage.setItem(key, JSON.stringify(item));
    },
    
    get: function(key) {
        const item = localStorage.getItem(key);
        if (!item) return null;
        
        const parsedItem = JSON.parse(item);
        const now = new Date().getTime();
        
        if (now - parsedItem.timestamp > parsedItem.expiration) {
            localStorage.removeItem(key);
            return null;
        }
        
        return parsedItem.data;
    },
    
    clear: function() {
        localStorage.clear();
    }
};

// 日志记录
const Logger = {
    log: function(action, details) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            action: action,
            details: details,
            userId: getCurrentUser()?.id || 'anonymous'
        };
        
        // 将日志发送到服务器
        fetch('/api/logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(logEntry)
        });
        
        // 同时保存到本地存储
        const logs = JSON.parse(localStorage.getItem('operationLogs') || '[]');
        logs.push(logEntry);
        localStorage.setItem('operationLogs', JSON.stringify(logs.slice(-100))); // 只保留最近100条
    }
};

// WebSocket连接管理
const WebSocketManager = {
    socket: null,
    
    connect: function() {
        this.socket = new WebSocket('ws://your-server-url/ws');
        
        this.socket.onopen = () => {
            console.log('WebSocket连接已建立');
        };
        
        this.socket.onmessage = (event) => {
            const notification = JSON.parse(event.data);
            this.handleNotification(notification);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket连接已关闭，尝试重连...');
            setTimeout(() => this.connect(), 5000);
        };
    },
    
    handleNotification: function(notification) {
        // 创建通知
        const notificationElement = document.createElement('div');
        notificationElement.className = 'notification';
        notificationElement.innerHTML = `
            <div class="notification-content">
                <h4>${notification.title}</h4>
                <p>${notification.message}</p>
            </div>
        `;
        
        document.body.appendChild(notificationElement);
        
        // 3秒后自动消失
        setTimeout(() => {
            notificationElement.remove();
        }, 3000);
    }
}; 