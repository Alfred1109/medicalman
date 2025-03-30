// 初始化患者趋势图
function initPatientTrendChart() {
    // 选择第一个图表容器
    const container = document.querySelector('.chart-container');
    
    // 初始化图表
    const patientTrendChart = Utils.chart.initChart(container.id, {
        title: {
            text: '患者就诊趋势'
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['就诊人次']
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: ['加载中...']
        },
        yAxis: {
            type: 'value',
            name: '人次'
        },
        series: [
            {
                name: '就诊人次',
                type: 'line',
                data: [],
                smooth: true,
                areaStyle: {}
            }
        ]
    });
    
    // 加载数据
    loadPatientTrendData(patientTrendChart);
    
    return patientTrendChart;
}

// 加载患者就诊趋势数据
function loadPatientTrendData(chart) {
    // 获取当前日期和一个月前的日期
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(endDate.getMonth() - 1);
    
    // 格式化日期
    const formatDate = date => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // 显示加载状态
    Utils.chart.showLoading(chart);
    
    // 发送请求
    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        // 隐藏加载状态
        Utils.chart.hideLoading(chart);
        
        if (result.success && result.data && result.data.charts && result.data.charts.outpatientTrend) {
            // 处理患者趋势数据
            updatePatientTrendChart(result.data.charts.outpatientTrend);
        } else {
            console.error('获取患者趋势数据失败:', result.message || '未知错误');
            Utils.chart.showError(chart, '获取数据失败');
        }
    })
    .catch(error => {
        console.error('加载患者趋势数据时出错:', error);
        Utils.chart.hideLoading(chart);
        Utils.chart.showError(chart, '网络请求失败');
    });
}

// 更新患者趋势图
function updatePatientTrendChart(data) {
    if (!data) return;
    
    // 准备x轴数据 - 使用门诊趋势的xAxis数据
    const xAxisData = data.xAxis || [];
    
    // 准备series数据 - 使用门诊趋势的第一个series数据
    const seriesData = data.series && data.series.length > 0 ? 
        data.series[0].data || [] : [];
    
    // 更新图表
    const chart = Utils.chart.getChart();
    if (chart) {
        chart.setOption({
            xAxis: {
                data: xAxisData
            },
            series: [
                {
                    data: seriesData
                }
            ]
        });
    }
}

// 获取患者就诊分布数据
function loadPatientDistribution(startDate, endDate) {
    const loadingIndicator = document.getElementById('patient-distribution-loading');
    if (loadingIndicator) loadingIndicator.style.display = 'block';

    fetch(`/dashboard/api/metrics_get?date_range=month&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        // 更新图表
        if (data.success) {
            updatePatientDistributionChart(data.data.charts.inpatientDistribution);
        } else {
            console.error('获取患者分布数据失败:', data.error || '未知错误');
            // 使用备用数据
            updatePatientDistributionChart(generateFallbackDistributionData());
        }
    })
    .catch(error => {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        console.error('加载患者分布数据时出错:', error);
        // 使用备用数据
        updatePatientDistributionChart(generateFallbackDistributionData());
    });
} 