// 加载科室工作量数据
function loadDepartmentWorkload(startDate, endDate) {
    fetch(`/api/dashboard/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.data && result.data.charts && result.data.charts.departmentWorkload) {
            updateDepartmentWorkloadChart(result.data.charts.departmentWorkload);
            hideLoading(workloadChart);
        } else {
            showError(workloadChart, '获取科室工作量数据失败');
            console.error('获取科室工作量数据失败:', result.message || '未知错误');
        }
    })
    .catch(error => {
        console.error('请求科室工作量数据时出错:', error);
        showError(workloadChart, '获取科室工作量数据失败');
    });
}

// 加载科室效率数据
function loadDepartmentEfficiency(startDate, endDate) {
    fetch(`/api/dashboard/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.data && result.data.charts && result.data.charts.outpatientTrend) {
            // 使用门诊量趋势数据来模拟科室效率
            updateDepartmentEfficiencyChart(result.data.charts.outpatientTrend);
            hideLoading(efficiencyChart);
        } else {
            showError(efficiencyChart, '获取科室效率数据失败');
            console.error('获取科室效率数据失败:', result.message || '未知错误');
        }
    })
    .catch(error => {
        console.error('请求科室效率数据时出错:', error);
        showError(efficiencyChart, '获取科室效率数据失败');
    });
}

// 加载科室资源数据
function loadDepartmentResources(startDate, endDate) {
    fetch(`/api/dashboard/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.data && result.data.charts && result.data.charts.departmentWorkload) {
            // 使用科室工作量数据来模拟科室资源
            updateDepartmentResourcesChart(result.data.charts.departmentWorkload);
            hideLoading(resourcesChart);
        } else {
            showError(resourcesChart, '获取科室资源数据失败');
            console.error('获取科室资源数据失败:', result.message || '未知错误');
        }
    })
    .catch(error => {
        console.error('请求科室资源数据时出错:', error);
        showError(resourcesChart, '获取科室资源数据失败');
    });
}

// 加载科室质量数据
function loadDepartmentQuality(startDate, endDate) {
    fetch(`/api/dashboard/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.data && result.data.charts && result.data.charts.inpatientDistribution) {
            // 使用住院患者分布数据来模拟科室质量
            updateDepartmentQualityChart(result.data.charts.inpatientDistribution);
            hideLoading(qualityChart);
        } else {
            showError(qualityChart, '获取科室质量数据失败');
            console.error('获取科室质量数据失败:', result.message || '未知错误');
        }
    })
    .catch(error => {
        console.error('请求科室质量数据时出错:', error);
        showError(qualityChart, '获取科室质量数据失败');
    });
}

// 加载内科数据
function loadInternalMedicineData(startDate, endDate) {
    const loadingIndicator = document.getElementById('internal-medicine-loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        if (data.success) {
            updateInternalMedicineChart(data.data);
        } else {
            console.error('获取内科数据失败:', data.error || '未知错误');
            updateInternalMedicineChart(null); // 使用默认数据
        }
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        console.error('加载内科数据时出错:', error);
        updateInternalMedicineChart(null); // 使用默认数据
    });
}

// 加载外科数据
function loadSurgeryData(startDate, endDate) {
    const loadingIndicator = document.getElementById('surgery-loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        if (data.success) {
            updateSurgeryChart(data.data);
        } else {
            console.error('获取外科数据失败:', data.error || '未知错误');
            updateSurgeryChart(null); // 使用默认数据
        }
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        console.error('加载外科数据时出错:', error);
        updateSurgeryChart(null); // 使用默认数据
    });
}

// 加载儿科数据
function loadPediatricsData(startDate, endDate) {
    const loadingIndicator = document.getElementById('pediatrics-loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        if (data.success) {
            updatePediatricsChart(data.data);
        } else {
            console.error('获取儿科数据失败:', data.error || '未知错误');
            updatePediatricsChart(null); // 使用默认数据
        }
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        console.error('加载儿科数据时出错:', error);
        updatePediatricsChart(null); // 使用默认数据
    });
}

// 加载妇产科数据
function loadObstetricsData(startDate, endDate) {
    const loadingIndicator = document.getElementById('obstetrics-loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${startDate}&end_date=${endDate}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        if (data.success) {
            updateObstetricsChart(data.data);
        } else {
            console.error('获取妇产科数据失败:', data.error || '未知错误');
            updateObstetricsChart(null); // 使用默认数据
        }
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        console.error('加载妇产科数据时出错:', error);
        updateObstetricsChart(null); // 使用默认数据
    });
} 