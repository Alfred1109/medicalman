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