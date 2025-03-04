// DRG分析页面的JavaScript代码

document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 添加过滤器变化事件监听
    document.getElementById('timeRange').addEventListener('change', updateData);
    document.getElementById('department').addEventListener('change', updateData);
    document.getElementById('drgGroup').addEventListener('change', updateData);
});

// 初始化页面
function initPage() {
    // 加载科室和DRG组选项
    loadFilterOptions();
    
    // 加载摘要数据
    loadSummaryData();
    
    // 加载图表数据
    loadChartData();
    
    // 加载表格数据
    loadTableData();
}

// 加载过滤器选项
function loadFilterOptions() {
    // 加载科室选项
    fetch('/api/departments')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const departmentSelect = document.getElementById('department');
                data.data.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept;
                    option.textContent = dept;
                    departmentSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('加载科室数据失败:', error));
    
    // 加载DRG组选项
    const drgGroupData = {
        time_range: getTimeRange(),
        department: getDepartment()
    };
    
    fetch('/api/drg/groups', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(drgGroupData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const drgGroupSelect = document.getElementById('drgGroup');
                // 清除现有选项（保留"全部"选项）
                while (drgGroupSelect.options.length > 1) {
                    drgGroupSelect.remove(1);
                }
                
                data.data.forEach(group => {
                    const option = document.createElement('option');
                    option.value = group.drg_group;
                    option.textContent = `${group.drg_group} (${group.case_count}例)`;
                    drgGroupSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('加载DRG组数据失败:', error));
}

// 加载摘要数据
function loadSummaryData() {
    const summaryData = {
        time_range: getTimeRange(),
        department: getDepartment(),
        drg_group: getDrgGroup()
    };
    
    fetch('/api/drg/summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(summaryData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSummaryCards(data.data);
            }
        })
        .catch(error => console.error('加载摘要数据失败:', error));
}

// 更新摘要卡片
function updateSummaryCards(data) {
    // CMI值
    updateCard('cmi', data.cmi.value, data.cmi.change);
    
    // 费用消耗指数
    updateCard('cost-index', data.cost_index.value, data.cost_index.change);
    
    // 时间消耗指数
    updateCard('time-index', data.time_index.value, data.time_index.change);
    
    // DRG组数
    updateCard('drg-count', data.drg_count.value, data.drg_count.change);
}

// 更新单个卡片
function updateCard(id, value, change) {
    const cardValue = document.getElementById(`${id}-value`);
    const cardChange = document.getElementById(`${id}-change`);
    const cardIcon = document.getElementById(`${id}-icon`);
    
    if (cardValue) {
        cardValue.textContent = value.toFixed(2);
    }
    
    if (cardChange && cardIcon) {
        const isPositive = change > 0;
        const changeClass = isPositive ? 'change-up' : 'change-down';
        const iconClass = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
        
        cardChange.textContent = `${isPositive ? '+' : ''}${change.toFixed(2)}%`;
        cardChange.className = changeClass;
        
        cardIcon.className = `fas ${iconClass} ${changeClass}`;
    }
}

// 加载图表数据
function loadChartData() {
    // 加载DRG组分布图表
    loadDistributionChart();
    
    // 加载CMI趋势图表
    loadTrendChart();
    
    // 加载象限分析图表
    loadQuadrantChart();
    
    // 加载RW区间分布图表
    loadRWDistributionChart();
}

// 加载DRG组分布图表
function loadDistributionChart() {
    const distributionData = {
        time_range: getTimeRange(),
        department: getDepartment()
    };
    
    fetch('/api/drg/distribution', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(distributionData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const ctx = document.getElementById('drgDistributionChart').getContext('2d');
                
                // 销毁现有图表
                if (window.drgDistributionChart) {
                    window.drgDistributionChart.destroy();
                }
                
                // 创建新图表
                window.drgDistributionChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: data.data.labels,
                        datasets: [{
                            data: data.data.values,
                            backgroundColor: [
                                'rgba(54, 162, 235, 0.8)',
                                'rgba(255, 99, 132, 0.8)',
                                'rgba(255, 206, 86, 0.8)',
                                'rgba(75, 192, 192, 0.8)',
                                'rgba(153, 102, 255, 0.8)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right'
                            },
                            title: {
                                display: true,
                                text: 'DRG组分布'
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error('加载DRG分布数据失败:', error));
}

// 加载CMI趋势图表
function loadTrendChart() {
    const trendData = {
        time_range: getTimeRange(),
        department: getDepartment(),
        drg_group: getDrgGroup(),
        metric: 'cmi',
        period: 'day'
    };
    
    fetch('/api/drg/trend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(trendData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const ctx = document.getElementById('cmiTrendChart').getContext('2d');
                
                // 销毁现有图表
                if (window.cmiTrendChart) {
                    window.cmiTrendChart.destroy();
                }
                
                // 创建新图表
                window.cmiTrendChart = new Chart(ctx, data.data.chart);
            }
        })
        .catch(error => console.error('加载CMI趋势数据失败:', error));
}

// 加载象限分析图表
function loadQuadrantChart() {
    // 这里可以添加象限分析图表的加载逻辑
    // 基于PDF中提到的"CMI和结余两个维度的病组象限分析"
    const ctx = document.getElementById('quadrantChart').getContext('2d');
    
    // 销毁现有图表
    if (window.quadrantChart) {
        window.quadrantChart.destroy();
    }
    
    // 创建新图表 - 这里使用模拟数据
    window.quadrantChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: '优势病组',
                    data: [
                        { x: 1.5, y: 0.3 },
                        { x: 1.6, y: 0.4 },
                        { x: 1.7, y: 0.5 }
                    ],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)'
                },
                {
                    label: '竞争病组',
                    data: [
                        { x: 0.8, y: 0.2 },
                        { x: 0.9, y: 0.3 },
                        { x: 0.7, y: 0.4 }
                    ],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                },
                {
                    label: '潜力病组',
                    data: [
                        { x: 1.4, y: -0.2 },
                        { x: 1.5, y: -0.3 },
                        { x: 1.6, y: -0.1 }
                    ],
                    backgroundColor: 'rgba(255, 206, 86, 0.8)'
                },
                {
                    label: '问题病组',
                    data: [
                        { x: 0.7, y: -0.3 },
                        { x: 0.8, y: -0.4 },
                        { x: 0.9, y: -0.2 }
                    ],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'CMI和结余象限分析'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'CMI值'
                    },
                    grid: {
                        drawOnChartArea: true
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '结余率'
                    },
                    grid: {
                        drawOnChartArea: true
                    }
                }
            }
        }
    });
}

// 加载RW区间分布图表
function loadRWDistributionChart() {
    // 这里可以添加RW区间分布图表的加载逻辑
    // 基于PDF中提到的"RW区间分布占比及费用分析"
    const ctx = document.getElementById('rwDistributionChart').getContext('2d');
    
    // 销毁现有图表
    if (window.rwDistributionChart) {
        window.rwDistributionChart.destroy();
    }
    
    // 创建新图表 - 这里使用模拟数据
    window.rwDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['3000以内', '3000-5000', '5000-8000', '8000以上'],
            datasets: [{
                label: '病例数量',
                data: [15, 25, 40, 20],
                backgroundColor: 'rgba(54, 162, 235, 0.8)'
            }, {
                label: '费用占比',
                data: [5, 20, 45, 30],
                backgroundColor: 'rgba(255, 99, 132, 0.8)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'RW区间分布及费用分析'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '百分比 (%)'
                    }
                }
            }
        }
    });
}

// 加载表格数据
function loadTableData() {
    const tableData = {
        time_range: getTimeRange(),
        department: getDepartment(),
        drg_group: getDrgGroup(),
        page: 1,
        page_size: 10
    };
    
    fetch('/api/drg/details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(tableData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTable(data.data.records);
            }
        })
        .catch(error => console.error('加载表格数据失败:', error));
}

// 更新表格
function updateTable(records) {
    const tableBody = document.getElementById('drgTableBody');
    
    // 清空表格
    tableBody.innerHTML = '';
    
    // 添加新数据
    records.forEach(record => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${record.drg_group}</td>
            <td>${record.department}</td>
            <td>${record.weight_score.toFixed(2)}</td>
            <td>${record.cost_index.toFixed(2)}</td>
            <td>${record.time_index.toFixed(2)}</td>
            <td>${record.total_cost.toFixed(2)}</td>
            <td>${record.length_of_stay}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// 更新数据
function updateData() {
    // 重新加载所有数据
    loadSummaryData();
    loadChartData();
    loadTableData();
}

// 获取时间范围
function getTimeRange() {
    return parseInt(document.getElementById('timeRange').value) || 30;
}

// 获取科室
function getDepartment() {
    return document.getElementById('department').value || '';
}

// 获取DRG组
function getDrgGroup() {
    return document.getElementById('drgGroup').value || '';
}

// 导出数据
function exportData() {
    const data = {
        time_range: getTimeRange(),
        department: getDepartment(),
        drg_group: getDrgGroup()
    };
    
    // 创建一个下载链接
    const a = document.createElement('a');
    a.href = `/api/drg/export?data=${encodeURIComponent(JSON.stringify(data))}`;
    a.download = 'drg_data.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
} 