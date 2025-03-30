// 初始化文件上传相关功能
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (!uploadArea || !fileInput) {
        console.warn('文件上传相关元素不存在');
        return;
    }
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 拖拽文件
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
        uploadArea.style.backgroundColor = 'var(--primary-light)';
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.backgroundColor = 'transparent';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.backgroundColor = 'transparent';
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
    
    // 文件选择处理
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
        // 重置input，允许重复上传相同文件
        fileInput.value = '';
    });
});

// 处理文件上传
function handleFiles(files) {
    if (!files || files.length === 0) return;
    
    // 显示上传进度
    const uploadStatus = document.createElement('div');
    uploadStatus.className = 'upload-status';
    uploadStatus.innerHTML = `<div class="upload-progress">上传中 (0/${files.length})...</div>`;
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.appendChild(uploadStatus);
    }
    
    // 处理每个文件
    Array.from(files).forEach((file, index) => {
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        
        // 发送上传请求
        fetch('/chat/upload', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`上传失败: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // 更新上传进度
            uploadStatus.innerHTML = `<div class="upload-progress">上传中 (${index + 1}/${files.length})...</div>`;
            
            // 添加文件到列表
            addFileToList(file.name, data.file_id);
            
            // 上传完成后移除状态显示
            if (index === files.length - 1) {
                setTimeout(() => {
                    uploadStatus.remove();
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('上传出错，请重试');
        });
    });
}

// 添加文件到显示列表
function addFileToList(fileName, fileId) {
    const uploadedFiles = document.getElementById('uploadedFiles');
    if (!uploadedFiles) return;
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <span class="file-name">${fileName}</span>
        <button class="file-remove" data-id="${fileId}">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // 添加删除事件
    const removeButton = fileItem.querySelector('.file-remove');
    removeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        // 发送删除请求
        fetch(`/chat/file/${fileId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.ok) {
                fileItem.remove();
            }
        })
        .catch(error => {
            console.error('删除文件错误:', error);
        });
    });
    
    uploadedFiles.appendChild(fileItem);
}

// 导出函数到全局作用域
window.FileUpload = {
    handleFiles,
    addFileToList
}; 