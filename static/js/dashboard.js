// 仪表盘数据管理
class DashboardManager {
    constructor() {
        this.charts = {};
        this.dateRange = 'week';
        this.initializeCharts();
        this.bindEvents();
        this.loadData();
    }

    // 初始化所有图表
    initializeCharts() {
        // 门诊量趋势图
        this.charts.outpatientTrend = echarts.init(document.getElementById('outpatient-trend-chart'));
        this.charts.outpatientTrend.setOption({
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            },
            yAxis: {
                type: 'value'
            },
            series: [{
                data: [150, 230, 224, 218, 135, 147, 260],
                type: 'line',
                smooth: true
            }]
        });

        // 收入构成图
        this.charts.revenueComposition = echarts.init(document.getElementById('revenue-composition-chart'));
        this.charts.revenueComposition.setOption({
            tooltip: {
                trigger: 'item'
            },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [{
                type: 'pie',
                radius: '50%',
                data: [
                    { value: 1048, name: '门诊收入' },
                    { value: 735, name: '住院收入' },
                    { value: 580, name: '药品收入' },
                    { value: 484, name: '检查收入' }
                ],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        });

        // 科室工作量图
        this.charts.departmentWorkload = echarts.init(document.getElementById('department-workload-chart'));
        this.charts.departmentWorkload.setOption({
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            xAxis: {
                type: 'value'
            },
            yAxis: {
                type: 'category',
                data: ['内科', '外科', '儿科', '妇产科', '骨科']
            },
            series: [{
                name: '工作量',
                type: 'bar',
                data: [320, 302, 301, 334, 390]
            }]
        });

        // 住院患者分布图
        this.charts.inpatientDistribution = echarts.init(document.getElementById('inpatient-distribution-chart'));
        this.charts.inpatientDistribution.setOption({
            tooltip: {
                trigger: 'item'
            },
            legend: {
                orient: 'vertical',
                left: 'left'
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '20',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: [
                    { value: 1048, name: '普通病房' },
                    { value: 735, name: '重症监护' },
                    { value: 580, name: '特需病房' },
                    { value: 484, name: '康复病房' }
                ]
            }]
        });
    }

    // 绑定事件
    bindEvents() {
        // 日期范围选择
        document.getElementById('date-range').addEventListener('change', (e) => {
            this.dateRange = e.target.value;
            const customRange = document.getElementById('custom-date-range');
            customRange.style.display = this.dateRange === 'custom' ? 'block' : 'none';
            this.loadData();
        });

        // 刷新按钮
        document.getElementById('refresh-dashboard').addEventListener('click', () => {
            this.loadData();
        });

        // 导出按钮
        document.getElementById('export-dashboard').addEventListener('click', () => {
            this.exportDashboard();
        });

        // 窗口大小改变时重绘图表
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => chart.resize());
        });
    }

    // 加载数据
    async loadData() {
        try {
            // 获取日期范围参数
            let startDate = null;
            let endDate = null;
            
            if (this.dateRange === 'custom') {
                startDate = document.getElementById('start-date').value;
                endDate = document.getElementById('end-date').value;
            }
            
            const response = await fetch('/api/dashboard/metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    date_range: this.dateRange,
                    start_date: startDate,
                    end_date: endDate
                })
            });
            
            if (response.status === 401) {
                // 未授权，需要登录
                const data = await response.json();
                if (data.redirect) {
                    window.location.href = data.redirect;
                    return;
                } else {
                    window.location.href = '/auth/login';
                    return;
                }
            }
            
            if (!response.ok) {
                throw new Error(`请求失败: ${response.status}`);
            }
            
            const responseData = await response.json();
            
            // 打印完整的API响应以便调试
            console.log('API完整响应:', JSON.stringify(responseData, null, 2));
            
            // 检查响应数据结构
            if (!responseData.success) {
                throw new Error(responseData.message || '获取数据失败');
            }
            
            // 使用正确的数据
            const data = responseData.data;
            console.log('API返回的数据结构:', Object.keys(data));
            
            // 安全地检查并更新统计数据
            if (data && data.metrics) {
                console.log('metrics数据结构:', Object.keys(data.metrics));
                
                // 确保所有必需的统计数据都存在
                if (!data.metrics.outpatient) {
                    console.warn('缺少outpatient统计数据，创建默认值');
                    data.metrics.outpatient = { count: '0', change: 0 };
                }
                if (!data.metrics.inpatient) {
                    console.warn('缺少inpatient统计数据，创建默认值');
                    data.metrics.inpatient = { count: '0', change: 0 };
                }
                if (!data.metrics.revenue) {
                    console.warn('缺少revenue统计数据，创建默认值');
                    data.metrics.revenue = { amount: '¥0', change: 0 };
                }
                if (!data.metrics.bedUsage) {
                    console.warn('缺少bedUsage统计数据，创建默认值');
                    data.metrics.bedUsage = { rate: '0%', change: 0 };
                }
                
                this.updateStats(data.metrics);
            } else {
                console.warn('缺少统计数据或格式不正确:', data);
                // 创建默认的统计数据以避免错误
                this.updateStats({
                    outpatient: { count: '0', change: 0 },
                    inpatient: { count: '0', change: 0 },
                    revenue: { amount: '¥0', change: 0 },
                    bedUsage: { rate: '0%', change: 0 }
                });
            }
            
            // 安全地检查并更新警报表格
            if (data && data.alerts) {
                this.updateAlertsTable(data.alerts);
            } else {
                console.warn('缺少警报数据或格式不正确');
                this.updateAlertsTable([]);
            }
            
            // 安全地检查并更新图表数据
            if (data && data.charts) {
                this.updateCharts(data.charts);
            } else {
                console.warn('缺少图表数据或格式不正确');
                // 创建默认的图表数据
                this.updateCharts({
                    outpatientTrend: { xAxis: [], series: [{ data: [], type: 'line', smooth: true }] },
                    revenueComposition: { data: [] },
                    departmentWorkload: { yAxis: [], series: [] },
                    inpatientDistribution: { legend: [], data: [] }
                });
            }
        } catch (error) {
            console.error('加载数据失败:', error);
            // 显示错误提示
            this.showError('数据加载失败: ' + error.message);
        }
    }

    // 更新统计数据
    updateStats(stats) {
        if (!stats) {
            console.warn('传入的stats对象为空');
            return;
        }
        
        try {
            // 更新各个统计卡片
            // 门诊量
            const outpatientValue = document.getElementById('outpatient-count');
            const outpatientChange = document.getElementById('outpatient-change');
            if (outpatientValue) {
                if (stats.outpatient && typeof stats.outpatient === 'object') {
                    outpatientValue.textContent = stats.outpatient.count || "0";
                    if (outpatientChange && typeof stats.outpatient.change !== 'undefined') {
                        const changeValue = parseFloat(stats.outpatient.change) || 0;
                        outpatientChange.innerHTML = `<i class="fas fa-arrow-${changeValue > 0 ? 'up' : 'down'}"></i> ${Math.abs(changeValue)}%`;
                    }
                } else {
                    outpatientValue.textContent = "0";
                    if (outpatientChange) outpatientChange.innerHTML = `<i class="fas fa-minus"></i> 0%`;
                }
            }
            
            // 住院量
            const inpatientValue = document.getElementById('inpatient-count');
            const inpatientChange = document.getElementById('inpatient-change');
            if (inpatientValue) {
                if (stats.inpatient && typeof stats.inpatient === 'object') {
                    inpatientValue.textContent = stats.inpatient.count || "0";
                    if (inpatientChange && typeof stats.inpatient.change !== 'undefined') {
                        const changeValue = parseFloat(stats.inpatient.change) || 0;
                        inpatientChange.innerHTML = `<i class="fas fa-arrow-${changeValue > 0 ? 'up' : 'down'}"></i> ${Math.abs(changeValue)}%`;
                    }
                } else {
                    inpatientValue.textContent = "0";
                    if (inpatientChange) inpatientChange.innerHTML = `<i class="fas fa-minus"></i> 0%`;
                }
            }
            
            // 收入
            const revenueValue = document.getElementById('revenue-amount');
            const revenueChange = document.getElementById('revenue-change');
            if (revenueValue) {
                if (stats.revenue && typeof stats.revenue === 'object') {
                    revenueValue.textContent = stats.revenue.amount || "¥0";
                    if (revenueChange && typeof stats.revenue.change !== 'undefined') {
                        const changeValue = parseFloat(stats.revenue.change) || 0;
                        revenueChange.innerHTML = `<i class="fas fa-arrow-${changeValue > 0 ? 'up' : 'down'}"></i> ${Math.abs(changeValue)}%`;
                    }
                } else {
                    revenueValue.textContent = "¥0";
                    if (revenueChange) revenueChange.innerHTML = `<i class="fas fa-minus"></i> 0%`;
                }
            }
            
            // 床位使用率
            const bedUsageValue = document.getElementById('bed-usage');
            const bedUsageChange = document.getElementById('bed-usage-change');
            if (bedUsageValue) {
                if (stats.bedUsage && typeof stats.bedUsage === 'object') {
                    bedUsageValue.textContent = stats.bedUsage.rate || "0%";
                    if (bedUsageChange && typeof stats.bedUsage.change !== 'undefined') {
                        const changeValue = parseFloat(stats.bedUsage.change) || 0;
                        bedUsageChange.innerHTML = `<i class="fas fa-arrow-${changeValue > 0 ? 'up' : 'down'}"></i> ${Math.abs(changeValue)}%`;
                    }
                } else {
                    bedUsageValue.textContent = "0%";
                    if (bedUsageChange) bedUsageChange.innerHTML = `<i class="fas fa-minus"></i> 0%`;
                }
            }
        } catch (error) {
            console.error('更新统计数据时出错:', error);
        }
    }

    // 更新警报表格
    updateAlertsTable(alerts) {
        if (!alerts) {
            console.warn('传入的alerts数组为空');
            return;
        }
        
        try {
            const tbody = document.getElementById('alerts-table-body');
            if (!tbody) {
                console.error('未找到警报表格 DOM 元素');
                return;
            }
            
            if (!Array.isArray(alerts) || alerts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无警报</td></tr>';
                return;
            }
            
            tbody.innerHTML = alerts.map(alert => {
                try {
                    // 处理不同格式的警报数据
                    if (Array.isArray(alert)) {
                        // 如果是数组格式，按照索引取值
                        return `
                            <tr>
                                <td>${alert[0] || ''}</td>
                                <td><span class="badge bg-${this.getAlertTypeClass(alert[1])}">${alert[1] || ''}</span></td>
                                <td>${alert[2] || ''}</td>
                                <td><span class="badge bg-${this.getStatusClass(alert[3])}">${alert[3] || ''}</span></td>
                                <td><button class="btn btn-sm btn-outline-primary alert-action" data-id="${alert[5] || ''}">${alert[4] || '处理'}</button></td>
                            </tr>
                        `;
                    } else if (typeof alert === 'object' && alert !== null) {
                        // 如果是对象格式，按照属性名取值
                        return `
                            <tr>
                                <td>${alert.time || alert.alert_time || ''}</td>
                                <td><span class="badge bg-${this.getAlertTypeClass(alert.type || alert.alert_type)}">${alert.typeText || alert.type || alert.alert_type || ''}</span></td>
                                <td>${alert.description || alert.message || ''}</td>
                                <td><span class="badge bg-${this.getStatusClass(alert.status)}">${alert.statusText || alert.status || ''}</span></td>
                                <td><button class="btn btn-sm btn-outline-primary alert-action" data-id="${alert.id || ''}">${alert.action || '处理'}</button></td>
                            </tr>
                        `;
                    } else {
                        return `<tr><td colspan="5" class="text-center">数据格式错误</td></tr>`;
                    }
                } catch (err) {
                    console.error('处理警报数据时出错:', err, alert);
                    return `<tr><td colspan="5" class="text-center">处理警报数据时出错</td></tr>`;
                }
            }).join('');
        } catch (error) {
            console.error('更新警报表格时出错:', error);
        }
    }
    
    // 获取警报类型对应的样式类
    getAlertTypeClass(type) {
        if (!type) return 'secondary';
        type = type.toString().toLowerCase();
        
        if (type.includes('danger') || type.includes('error') || type.includes('严重') || type.includes('critical'))
            return 'danger';
        if (type.includes('warning') || type.includes('警告') || type.includes('warn'))
            return 'warning';
        if (type.includes('info') || type.includes('信息'))
            return 'info';
        if (type.includes('success') || type.includes('成功'))
            return 'success';
            
        return 'secondary';
    }
    
    // 获取状态对应的样式类
    getStatusClass(status) {
        if (!status) return 'secondary';
        status = status.toString().toLowerCase();
        
        if (status.includes('pending') || status.includes('待处理') || status.includes('未处理'))
            return 'warning';
        if (status.includes('processing') || status.includes('处理中'))
            return 'primary';
        if (status.includes('resolved') || status.includes('已解决') || status.includes('已处理'))
            return 'success';
        if (status.includes('rejected') || status.includes('已拒绝') || status.includes('已忽略'))
            return 'danger';
            
        return 'secondary';
    }

    // 更新图表数据
    updateCharts(chartsData) {
        if (!chartsData) {
            console.warn('传入的chartsData对象为空');
            return;
        }
        
        console.log('更新图表数据:', chartsData);
        
        try {
            // 更新门诊量趋势图
            if (this.charts.outpatientTrend) {
                try {
                    console.log('更新门诊趋势图:', chartsData.outpatientTrend);
                    const options = {
                        xAxis: {
                            type: 'category',
                            data: chartsData.outpatientTrend?.xAxis || []
                        },
                        series: (chartsData.outpatientTrend?.series) || [{
                            data: [],
                            type: 'line',
                            smooth: true
                        }]
                    };
                    this.charts.outpatientTrend.setOption(options);
                } catch (err) {
                    console.error('更新门诊量趋势图出错:', err);
                }
            }
            
            // 更新收入构成图
            if (this.charts.revenueComposition) {
                try {
                    console.log('更新收入构成图:', chartsData.revenueComposition);
                    const options = {
                        series: [{
                            type: 'pie',
                            radius: '50%',
                            data: chartsData.revenueComposition?.data || [],
                            emphasis: {
                                itemStyle: {
                                    shadowBlur: 10,
                                    shadowOffsetX: 0,
                                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }
                            }
                        }]
                    };
                    this.charts.revenueComposition.setOption(options);
                } catch (err) {
                    console.error('更新收入构成图出错:', err);
                }
            }
            
            // 更新科室工作量图
            if (this.charts.departmentWorkload) {
                try {
                    console.log('更新科室工作量图:', chartsData.departmentWorkload);
                    const options = {
                        yAxis: {
                            type: 'category',
                            data: chartsData.departmentWorkload?.yAxis || []
                        },
                        series: chartsData.departmentWorkload?.series || [{
                            type: 'bar',
                            data: []
                        }]
                    };
                    this.charts.departmentWorkload.setOption(options);
                } catch (err) {
                    console.error('更新科室工作量图出错:', err);
                }
            }
            
            // 更新住院患者分布图
            if (this.charts.inpatientDistribution) {
                try {
                    console.log('更新住院患者分布图:', chartsData.inpatientDistribution);
                    const options = {
                        legend: {
                            orient: 'vertical',
                            left: 'left',
                            data: chartsData.inpatientDistribution?.legend || []
                        },
                        series: [{
                            type: 'pie',
                            radius: ['40%', '70%'],
                            avoidLabelOverlap: false,
                            data: chartsData.inpatientDistribution?.data || [],
                            itemStyle: {
                                borderRadius: 10,
                                borderColor: '#fff',
                                borderWidth: 2
                            },
                            label: {
                                show: false,
                                position: 'center'
                            },
                            emphasis: {
                                label: {
                                    show: true,
                                    fontSize: '20',
                                    fontWeight: 'bold'
                                }
                            },
                            labelLine: {
                                show: false
                            }
                        }]
                    };
                    this.charts.inpatientDistribution.setOption(options);
                } catch (err) {
                    console.error('更新住院患者分布图出错:', err);
                }
            }
        } catch (error) {
            console.error('更新图表时出错:', error);
        }
    }

    // 导出仪表盘数据
    exportDashboard() {
        // 这里应该实现导出功能
        alert('导出功能开发中...');
    }

    // 显示错误信息
    showError(message) {
        // 这里应该实现错误提示功能
        alert(message);
    }
}

// 初始化仪表盘
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
}); 