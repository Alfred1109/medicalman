// 仪表盘数据管理
(function() {
    // 仪表盘管理器类
    class DashboardManager {
        constructor() {
            this.charts = {}; // 图表实例
            this.dateRange = 'week'; // 默认日期范围
            this.startDate = null; // 自定义开始日期
            this.endDate = null; // 自定义结束日期
            this.isLoading = false; // 加载状态
            this.chartContainers = {
                outpatientTrend: 'outpatient-trend-chart',
                revenueComposition: 'revenue-composition-chart',
                departmentWorkload: 'department-workload-chart',
                inpatientDistribution: 'inpatient-distribution-chart'
            };
            
            // 检查HTML中的实际ID来确保这些ID映射是正确的
            console.log('[初始化] 检查核心指标元素:');
            console.log('outpatient-count:', !!document.getElementById('outpatient-count'));
            console.log('inpatient-count:', !!document.getElementById('inpatient-count'));
            console.log('revenue-amount:', !!document.getElementById('revenue-amount'));
            console.log('bed-usage:', !!document.getElementById('bed-usage'));
            
            this.metricsContainers = {
                outpatient: 'outpatient-count',
                inpatient: 'inpatient-count',
                revenue: 'revenue-amount',
                bedUsage: 'bed-usage'
            };
        }

        /**
         * 初始化仪表盘
         */
        init() {
            document.addEventListener('DOMContentLoaded', () => {
                // DOM加载完成后检查元素
                console.log('[DOMContentLoaded] 检查核心指标元素:');
                console.log('outpatient-count:', !!document.getElementById('outpatient-count'));
                console.log('inpatient-count:', !!document.getElementById('inpatient-count'));
                console.log('revenue-amount:', !!document.getElementById('revenue-amount'));
                console.log('bed-usage:', !!document.getElementById('bed-usage'));
                
                this.initCharts();
                this.bindEvents();
                this.loadData();
            });
        }

        /**
         * 初始化所有图表
         */
        initCharts() {
            // 检查容器是否存在
            const containers = Object.values(this.chartContainers);
            const missingContainers = containers.filter(id => !document.getElementById(id));
            
            if (missingContainers.length > 0) {
                console.warn(`找不到以下图表容器: ${missingContainers.join(', ')}`);
            }
            
            // 门诊趋势图
            this.initOutpatientTrendChart();
            
            // 收入构成图
            this.initRevenueCompositionChart();
            
            // 科室工作量图
            this.initDepartmentWorkloadChart();
            
            // 住院患者分布图
            this.initInpatientDistributionChart();
        }
        
        /**
         * 初始化门诊趋势图
         */
        initOutpatientTrendChart() {
            const containerId = this.chartContainers.outpatientTrend;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            this.charts.outpatientTrend = Utils.chart.initChart(container, {
                title: {
                    text: '门诊量趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                },
                yAxis: {
                    type: 'value',
                    name: '人次'
                },
                series: [{
                    name: '门诊量',
                    data: [150, 230, 224, 218, 135, 147, 260],
                    type: 'line'
                }]
            });
        }
        
        /**
         * 初始化收入构成图
         */
        initRevenueCompositionChart() {
            const containerId = this.chartContainers.revenueComposition;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            this.charts.revenueComposition = Utils.chart.initChart(container, {
                title: {
                    text: '收入构成'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    top: 'middle'
                },
                series: [{
                    name: '收入来源',
                    type: 'pie',
                    data: [
                        { value: 1048, name: '门诊收入' },
                        { value: 735, name: '住院收入' },
                        { value: 580, name: '药品收入' },
                        { value: 484, name: '检查收入' }
                    ]
                }]
            });
        }
        
        /**
         * 初始化科室工作量图
         */
        initDepartmentWorkloadChart() {
            const containerId = this.chartContainers.departmentWorkload;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            this.charts.departmentWorkload = Utils.chart.initChart(container, {
                title: {
                    text: '科室工作量'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                xAxis: {
                    type: 'value',
                    name: '工作量'
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
        }
        
        /**
         * 初始化住院患者分布图
         */
        initInpatientDistributionChart() {
            const containerId = this.chartContainers.inpatientDistribution;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            this.charts.inpatientDistribution = Utils.chart.initChart(container, {
                title: {
                    text: '住院患者分布'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    top: 'middle'
                },
                series: [{
                    name: '患者分布',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    label: {
                        show: true,
                        formatter: '{b}: {d}%'
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

        /**
         * 绑定事件处理函数
         */
        bindEvents() {
            // 日期范围选择
            const dateRangeSelect = document.getElementById('date-range');
            if (dateRangeSelect) {
                dateRangeSelect.addEventListener('change', (e) => {
                    this.dateRange = e.target.value;
                    
                    // 显示/隐藏自定义日期范围面板
                    const customRangePanel = document.getElementById('custom-date-range');
                    if (customRangePanel) {
                        customRangePanel.style.display = this.dateRange === 'custom' ? 'block' : 'none';
                    }
                    
                    // 如果不是自定义日期范围，立即加载数据
                    if (this.dateRange !== 'custom') {
                        this.loadData();
                    }
                });
            }
            
            // 自定义日期范围输入
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            
            if (startDateInput) {
                startDateInput.addEventListener('change', (e) => {
                    this.startDate = e.target.value;
                });
            }
            
            if (endDateInput) {
                endDateInput.addEventListener('change', (e) => {
                    this.endDate = e.target.value;
                });
            }

            // 刷新按钮
            const refreshButton = document.getElementById('refresh-dashboard');
            if (refreshButton) {
                refreshButton.addEventListener('click', () => {
                    this.loadData(true);
                });
            }

            // 导出按钮
            const exportButton = document.getElementById('export-dashboard');
            if (exportButton) {
                exportButton.addEventListener('click', () => {
                    this.exportDashboard();
                });
            }
            
            // 绑定警报行点击事件
            this.bindAlertRowEvents();
        }
        
        /**
         * 绑定警报行点击事件
         */
        bindAlertRowEvents() {
            const alertsTable = document.getElementById('alerts-table');
            if (!alertsTable) return;
            
            alertsTable.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                if (!row) return;
                
                const alertId = row.dataset.alertId;
                if (!alertId) return;
                
                // 导航到警报详情页
                window.location.href = `/alerts/view/${alertId}`;
            });
        }

        /**
         * 显示加载状态
         */
        showLoading() {
            this.isLoading = true;
            
            // 显示图表加载状态
            Object.values(this.charts).forEach(chart => {
                if (chart) {
                    chart.showLoading({
                        text: '数据加载中...',
                        maskColor: 'rgba(255, 255, 255, 0.8)',
                        fontSize: 14
                    });
                }
            });
            
            // 显示全局加载指示器
            const loadingIndicator = document.getElementById('dashboard-loading');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
        }

        /**
         * 隐藏加载状态
         */
        hideLoading() {
            this.isLoading = false;
            
            // 隐藏图表加载状态
            Object.values(this.charts).forEach(chart => {
                if (chart) {
                    chart.hideLoading();
                }
            });
            
            // 隐藏全局加载指示器
            const loadingIndicator = document.getElementById('dashboard-loading');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }

        /**
         * 加载仪表盘数据
         * @param {boolean} forceRefresh - 是否强制刷新数据（忽略缓存）
         */
        async loadData(forceRefresh = false) {
            // 避免重复加载
            if (this.isLoading) return;
            
            try {
                this.showLoading();
                
                // 验证自定义日期范围
                if (this.dateRange === 'custom') {
                    if (!this.startDate || !this.endDate) {
                        this.showError('请选择开始和结束日期');
                        this.hideLoading();
                        return;
                    }
                }
                
                // 构建请求参数
                const params = {
                    date_range: this.dateRange
                };
                
                // 添加自定义日期范围参数
                if (this.dateRange === 'custom' && this.startDate && this.endDate) {
                    params.start_date = this.startDate;
                    params.end_date = this.endDate;
                }
                
                console.log(`请求仪表盘数据，参数:`, params);
                
                // 检查CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                console.log('当前CSRF token:', csrfToken);
                
                // 使用正确的API路径，改用POST请求
                console.log('开始发送API请求到:', '/api/dashboard/metrics');
                const response = await Utils.api.post('/api/dashboard/metrics', params, {
                    useCache: !forceRefresh
                });
                
                // 调试：打印完整响应
                console.log('API响应完整数据:', JSON.stringify(response, null, 2));
                
                // 检查前端DOM中关键元素是否存在
                console.log('关键DOM元素检查:');
                console.log('outpatient-count:', !!document.getElementById('outpatient-count'));
                console.log('inpatient-count:', !!document.getElementById('inpatient-count'));
                console.log('revenue-amount:', !!document.getElementById('revenue-amount'));
                console.log('bed-usage:', !!document.getElementById('bed-usage'));
                
                // 处理响应
                if (response && response.success && response.data) {
                    const data = response.data;
                    console.log('仪表盘数据加载成功', data);
                    
                    // 添加详细的数据结构检查
                    console.log('data完整结构:', data);
                    
                    if (!data.stats) {
                        console.error('数据结构不完整: stats字段不在预期位置');
                        console.log('尝试在data.data中查找stats字段');
                        
                        // 检查是否是嵌套结构 (data.data.stats)
                        if (data.data && data.data.stats) {
                            console.log('在data.data中找到了stats字段:', data.data.stats);
                            
                            // 更新图表和指标，添加try-catch以捕获可能的错误
                            try {
                                console.log('更新图表数据:', data.data.charts);
                                this.updateCharts(data.data);
                                console.log('更新统计指标:', data.data.stats);
                                this.updateMetrics(data.data.stats);
                                console.log('更新警报数据:', data.data.alerts || []);
                                this.updateAlerts(data.data.alerts || []);
                            } catch (err) {
                                console.error('更新仪表盘数据时出错:', err);
                                this.showError(`更新仪表盘数据时出错: ${err.message}`);
                                // 使用备用数据
                                this.updateChartsWithFallbackData();
                            }
                            return;
                        }
                        
                        this.showError('数据结构不完整: stats字段缺失');
                        this.updateChartsWithFallbackData();
                        return;
                    }
                    
                    // 更详细地检查stats结构
                    const statsKeys = Object.keys(data.stats || {});
                    console.log('stats包含的字段:', statsKeys);
                    if (!data.stats.outpatient) {
                        console.error('stats.outpatient字段缺失，完整的stats数据:', data.stats);
                    }
                    
                    // 更新图表和指标，添加try-catch以捕获可能的错误
                    try {
                        console.log('更新图表数据:', data.charts);
                        this.updateCharts(data);
                        console.log('更新统计指标:', data.stats);
                        this.updateMetrics(data.stats);
                        console.log('更新警报数据:', data.alerts || []);
                        this.updateAlerts(data.alerts || []);
                    } catch (err) {
                        console.error('更新仪表盘数据时出错:', err);
                        this.showError(`更新仪表盘数据时出错: ${err.message}`);
                        // 使用备用数据
                        this.updateChartsWithFallbackData();
                    }
                } else {
                    const errorMsg = response?.error || '服务器未返回有效数据';
                    console.error(`加载仪表盘数据失败: ${errorMsg}`);
                    console.error('错误响应完整信息:', response);
                    this.showError(`加载数据失败: ${errorMsg}`);
                    
                    // 即使API返回失败，也尝试从response.data获取可用数据
                    if (response && response.data) {
                        console.log('尝试使用error response中的data:', response.data);
                        
                        // 检查是否是嵌套结构 (response.data.data.stats)
                        if (response.data.data && response.data.data.stats) {
                            console.log('在response.data.data中找到了stats字段');
                            if (response.data.data.stats) {
                                console.log('更新统计指标:', response.data.data.stats);
                                this.updateMetrics(response.data.data.stats);
                            }
                            if (response.data.data.charts) {
                                console.log('更新图表数据:', response.data.data.charts);
                                this.updateCharts(response.data.data);
                            }
                            return;
                        }
                        
                        // 尝试非嵌套结构
                        if (response.data.stats) {
                            console.log('更新统计指标:', response.data.stats);
                            this.updateMetrics(response.data.stats);
                        }
                        if (response.data.charts) {
                            console.log('更新图表数据:', response.data.charts);
                            this.updateCharts(response.data);
                        }
                    } else {
                        // 使用备用数据
                        this.updateChartsWithFallbackData();
                    }
                }
            } catch (error) {
                console.error('加载仪表盘数据时出错:', error);
                this.showError('数据加载失败，请重试');
                
                // 使用备用数据
                this.updateChartsWithFallbackData();
            } finally {
                this.hideLoading();
            }
        }

        /**
         * 显示错误消息
         * @param {string} message - 错误消息
         */
        showError(message) {
            console.error(message);
            
            // 使用Toast或其他通知机制
            if (window.Utils && window.Utils.showToast) {
                window.Utils.showToast(message, 'error');
            } else {
                alert(message);
            }
        }

        /**
         * 更新图表数据
         * @param {Object} data - API返回的数据
         */
        updateCharts(data) {
            console.log('更新图表, 收到数据:', data);
            
            if (!data || !data.charts) {
                console.warn('没有图表数据可用，使用备用数据');
                this.updateChartsWithFallbackData();
                return;
            }
            
            const chartsData = data.charts;
            const missingCharts = [];
            
            // 更新门诊趋势图
            if (chartsData.outpatientTrend) {
                this.updateOutpatientTrendChart(chartsData.outpatientTrend);
            } else {
                missingCharts.push('outpatientTrend');
            }
            
            // 更新收入构成图
            if (chartsData.revenueComposition) {
                this.updateRevenueCompositionChart(chartsData.revenueComposition);
            } else {
                missingCharts.push('revenueComposition');
            }
            
            // 更新科室工作量图
            if (chartsData.departmentWorkload) {
                this.updateDepartmentWorkloadChart(chartsData.departmentWorkload);
            } else {
                missingCharts.push('departmentWorkload');
            }
            
            // 更新住院患者分布图
            if (chartsData.inpatientDistribution) {
                this.updateInpatientDistributionChart(chartsData.inpatientDistribution);
            } else {
                missingCharts.push('inpatientDistribution');
            }
            
            // 如果有缺失的图表，记录日志
            if (missingCharts.length > 0) {
                console.warn(`部分图表数据缺失: ${missingCharts.join(', ')}`);
            }
        }
        
        /**
         * 使用备用数据更新图表
         * 当API请求失败时使用此方法
         */
        updateChartsWithFallbackData() {
            console.log('使用备用数据更新图表');
            
            // 生成备用数据
            const trendData = this.generateMockTrendData();
            const compositionData = this.generateMockCompositionData();
            const workloadData = this.generateMockWorkloadData();
            const distributionData = this.generateMockDistributionData();
            
            // 更新各图表
            this.updateOutpatientTrendChart(trendData);
            this.updateRevenueCompositionChart(compositionData);
            this.updateDepartmentWorkloadChart(workloadData);
            this.updateInpatientDistributionChart(distributionData);
            
            // 更新指标卡片
            this.updateMetricsWithMockData();
        }
        
        /**
         * 生成门诊趋势的模拟数据
         */
        generateMockTrendData() {
            const days = 7;
            const dates = [];
            const data = [];
            
            const today = new Date();
            for (let i = days - 1; i >= 0; i--) {
                const date = new Date();
                date.setDate(today.getDate() - i);
                dates.push(date.toISOString().split('T')[0]);
                data.push(Math.floor(Math.random() * 500) + 100);
            }
            
            return {
                xAxis: {
                    data: dates
                },
                series: [{
                    name: '门诊量',
                    data: data
                }]
            };
        }
        
        /**
         * 生成收入构成的模拟数据
         */
        generateMockCompositionData() {
            return {
                data: [
                    { name: '门诊收入', value: Math.floor(Math.random() * 1000) + 500 },
                    { name: '住院收入', value: Math.floor(Math.random() * 800) + 400 },
                    { name: '药品收入', value: Math.floor(Math.random() * 600) + 300 },
                    { name: '检查收入', value: Math.floor(Math.random() * 400) + 200 },
                    { name: '其他收入', value: Math.floor(Math.random() * 200) + 100 }
                ]
            };
        }
        
        /**
         * 生成科室工作量的模拟数据
         */
        generateMockWorkloadData() {
            const departments = ['内科', '外科', '儿科', '妇产科', '骨科', '眼科', '神经科', '口腔科'];
            
            return {
                yAxis: {
                    data: departments
                },
                series: [
                    {
                        name: '门诊量',
                        data: departments.map(() => Math.floor(Math.random() * 300) + 100)
                    },
                    {
                        name: '住院量',
                        data: departments.map(() => Math.floor(Math.random() * 200) + 50)
                    },
                    {
                        name: '手术量',
                        data: departments.map(() => Math.floor(Math.random() * 100) + 20)
                    }
                ]
            };
        }
        
        /**
         * 生成住院患者分布的模拟数据
         */
        generateMockDistributionData() {
            return {
                legend: ['普通病房', '重症监护', '特需病房', '康复病房', '日间病房'],
                data: [
                    { name: '普通病房', value: Math.floor(Math.random() * 1000) + 500 },
                    { name: '重症监护', value: Math.floor(Math.random() * 200) + 100 },
                    { name: '特需病房', value: Math.floor(Math.random() * 300) + 150 },
                    { name: '康复病房', value: Math.floor(Math.random() * 400) + 200 },
                    { name: '日间病房', value: Math.floor(Math.random() * 150) + 80 }
                ]
            };
        }

        /**
         * 更新门诊趋势图表
         * @param {Object} data - 门诊趋势数据
         */
        updateOutpatientTrendChart(data) {
            const chart = this.charts.outpatientTrend;
            if (!chart) return;
            
            try {
                // 规范化数据结构
                const xAxisData = data.xAxis?.data || [];
                const seriesData = data.series?.[0]?.data || [];
                
                const option = {
                    xAxis: {
                        data: xAxisData
                    },
                    series: [{
                        name: '门诊量',
                        data: seriesData
                    }]
                };
                
                Utils.chart.updateChart(chart, option);
            } catch (error) {
                console.error('更新门诊趋势图表失败:', error);
            }
        }

        /**
         * 更新收入构成图表
         * @param {Object} data - 收入构成数据
         */
        updateRevenueCompositionChart(data) {
            const chart = this.charts.revenueComposition;
            if (!chart) return;
            
            try {
                // 规范化数据结构
                const pieData = data.data || [];
                
                const option = {
                    series: [{
                        data: pieData
                    }]
                };
                
                // 更新图例数据
                if (pieData.length > 0) {
                    option.legend = {
                        data: pieData.map(item => item.name)
                    };
                }
                
                Utils.chart.updateChart(chart, option);
            } catch (error) {
                console.error('更新收入构成图表失败:', error);
            }
        }

        /**
         * 更新科室工作量图表
         * @param {Object} data - 科室工作量数据
         */
        updateDepartmentWorkloadChart(data) {
            const chart = this.charts.departmentWorkload;
            if (!chart) return;
            
            try {
                // 规范化数据结构
                const departments = data.yAxis?.data || [];
                const series = data.series || [];
                
                const option = {
                    yAxis: {
                        data: departments
                    },
                    series: series
                };
                
                Utils.chart.updateChart(chart, option);
            } catch (error) {
                console.error('更新科室工作量图表失败:', error);
            }
        }

        /**
         * 更新住院分布图表
         * @param {Object} data - 住院分布数据
         */
        updateInpatientDistributionChart(data) {
            const chart = this.charts.inpatientDistribution;
            if (!chart) return;
            
            try {
                // 规范化数据结构
                const pieData = data.data || [];
                const legendData = data.legend || pieData.map(item => item.name);
                
                const option = {
                    legend: {
                        data: legendData
                    },
                    series: [{
                        data: pieData
                    }]
                };
                
                Utils.chart.updateChart(chart, option);
            } catch (error) {
                console.error('更新住院分布图表失败:', error);
            }
        }

        /**
         * 更新统计指标
         * @param {Object} metrics - 指标数据
         */
        updateMetrics(metrics) {
            console.log('更新metrics, 收到数据:', metrics);
            
            // 确保metrics是对象且不为null
            if (!metrics || typeof metrics !== 'object') {
                console.warn('没有指标数据可用或数据不是对象，使用备用数据', metrics);
                this.updateMetricsWithMockData();
                return;
            }
            
            // 检查metrics结构是否完整
            const required = ['outpatient', 'inpatient', 'revenue', 'bedUsage'];
            const missing = required.filter(key => !metrics[key]);
            
            if (missing.length > 0) {
                console.warn(`metrics数据不完整，缺少: ${missing.join(', ')}，使用备用数据`);
                console.log('收到的metrics数据:', metrics);
                // 对于某些应用场景，我们可能希望使用部分数据而不是完全回退到模拟数据
                // 这里选择使用完全的模拟数据，以确保UI的一致性
                this.updateMetricsWithMockData();
                return;
            }
            
            try {
                // 更新门诊量 - 添加防御性检查
                if (metrics.outpatient && typeof metrics.outpatient === 'object') {
                    console.log('更新门诊量指标:', metrics.outpatient);
                    this.updateMetric('outpatient', metrics.outpatient);
                } else {
                    console.warn('门诊量数据无效:', metrics.outpatient);
                }
                
                // 更新住院量 - 添加防御性检查
                if (metrics.inpatient && typeof metrics.inpatient === 'object') {
                    console.log('更新住院量指标:', metrics.inpatient);
                    this.updateMetric('inpatient', metrics.inpatient);
                } else {
                    console.warn('住院量数据无效:', metrics.inpatient);
                }
                
                // 更新收入 - 添加防御性检查
                if (metrics.revenue && typeof metrics.revenue === 'object') {
                    console.log('更新收入指标:', metrics.revenue);
                    this.updateMetric('revenue', metrics.revenue);
                } else {
                    console.warn('收入数据无效:', metrics.revenue);
                }
                
                // 更新床位使用率 - 添加防御性检查
                if (metrics.bedUsage && typeof metrics.bedUsage === 'object') {
                    console.log('更新床位使用率指标:', metrics.bedUsage);
                    this.updateMetric('bedUsage', metrics.bedUsage);
                } else {
                    console.warn('床位使用率数据无效:', metrics.bedUsage);
                }
            } catch (error) {
                console.error('更新指标时出错:', error);
                this.updateMetricsWithMockData();
            }
        }
        
        /**
         * 使用模拟数据更新指标
         */
        updateMetricsWithMockData() {
            const mockMetrics = {
                outpatient: {
                    value: `${Math.floor(Math.random() * 5000) + 1000}`,
                    change: (Math.random() * 10 - 5).toFixed(1)
                },
                inpatient: {
                    value: `${Math.floor(Math.random() * 500) + 100}`,
                    change: (Math.random() * 8 - 4).toFixed(1)
                },
                revenue: {
                    value: `¥${(Math.random() * 1000000 + 500000).toFixed(2)}`,
                    change: (Math.random() * 12 - 6).toFixed(1)
                },
                bedUsage: {
                    value: `${Math.floor(Math.random() * 20) + 75}%`,
                    change: (Math.random() * 5 - 2.5).toFixed(1)
                }
            };
            
            this.updateMetrics(mockMetrics);
        }
        
        /**
         * 更新单个指标
         * @param {string} key - 指标键名
         * @param {Object} data - 指标数据
         */
        updateMetric(key, data) {
            if (!key || !data) {
                console.warn(`无法更新指标 ${key}，数据无效:`, data);
                return;
            }
            
            // 确保data有基本结构
            if (typeof data !== 'object' || (data.value === undefined && data.count === undefined && data.rate === undefined && data.amount === undefined)) {
                console.warn(`指标 ${key} 数据结构不完整:`, data);
                return;
            }
            
            // 获取值元素
            const valueElementId = this.metricsContainers[key];
            console.log(`[updateMetric] 准备更新指标 ${key}, 元素ID:`, valueElementId);
            const valueElement = document.getElementById(valueElementId);
            
            if (!valueElement) {
                console.warn(`找不到指标值容器: ${valueElementId}`);
                // 尝试直接查找元素，不使用ID映射
                console.log(`尝试直接查找元素 #${key}-count 或 #${key}-amount 或 #${key}`);
                const altElement1 = document.getElementById(`${key}-count`);
                const altElement2 = document.getElementById(`${key}-amount`);
                const altElement3 = document.getElementById(key);
                
                if (altElement1) {
                    console.log(`找到替代元素 #${key}-count}`);
                    
                    // 支持两种数据结构格式: value 或 count
                    const displayValue = data.count !== undefined ? data.count : 
                                         data.value !== undefined ? data.value : '--';
                    altElement1.textContent = displayValue;
                    
                    // 尝试更新变化率元素
                    const changeElement = document.getElementById(`${key}-change`);
                    if (changeElement && (data.change !== undefined)) {
                        this.updateChangeElement(changeElement, data.change);
                    }
                    return;
                } else if (altElement2) {
                    console.log(`找到替代元素 #${key}-amount}`);
                    
                    // 支持两种数据结构格式: value 或 amount
                    const displayValue = data.amount !== undefined ? data.amount : 
                                         data.value !== undefined ? data.value : '--';
                    altElement2.textContent = displayValue;
                    
                    // 尝试更新变化率元素
                    const changeElement = document.getElementById(`${key}-change`);
                    if (changeElement && (data.change !== undefined)) {
                        this.updateChangeElement(changeElement, data.change);
                    }
                    return;
                } else if (altElement3) {
                    console.log(`找到替代元素 #${key}`);
                    
                    // 尝试各种可能的值
                    const displayValue = data.value !== undefined ? data.value :
                                         data.count !== undefined ? data.count :
                                         data.amount !== undefined ? data.amount :
                                         data.rate !== undefined ? data.rate + '%' : '--';
                    altElement3.textContent = displayValue;
                    
                    // 尝试更新变化率元素
                    const changeElement = document.getElementById(`${key}-change`);
                    if (changeElement && (data.change !== undefined)) {
                        this.updateChangeElement(changeElement, data.change);
                    }
                    return;
                }
                
                console.error(`所有尝试查找元素的方法都失败了，无法更新指标 ${key}`);
                return;
            }
            
            // 更新值 - 支持多种数据结构格式
            const displayValue = data.value !== undefined ? data.value :
                                data.count !== undefined ? data.count :
                                data.amount !== undefined ? data.amount :
                                data.rate !== undefined ? data.rate + '%' : '--';
                                
            console.log(`设置 ${key} 值为:`, displayValue);
            valueElement.textContent = displayValue;
            
            // 获取变化率元素 - 使用专门的ID
            const changeElementId = `${key}-change`;
            console.log(`寻找变化率元素:`, changeElementId);
            const changeElement = document.getElementById(changeElementId);
            
            // 更新变化率
            if (changeElement && data.change !== undefined) {
                this.updateChangeElement(changeElement, data.change);
            } else {
                console.warn(`无法更新变化率: 元素=${!!changeElement}, 数据=${data.change}`);
            }
        }
        
        /**
         * 更新变化率元素
         * @param {HTMLElement} changeElement - 变化率元素
         * @param {number|string} change - 变化率值
         */
        updateChangeElement(changeElement, change) {
            const numChange = parseFloat(change);
            const isPositive = numChange > 0;
            const changeText = `${isPositive ? '+' : ''}${numChange}%`;
            
            console.log(`设置变化率为:`, changeText, '是否为正值:', isPositive);
            
            // 清除现有内容并设置新的文本和图标
            changeElement.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i> ${changeText}
            `;
            
            // 更新样式类
            changeElement.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
            console.log(`更新样式类为: stat-change ${isPositive ? 'positive' : 'negative'}`);
        }

        /**
         * 更新警报列表
         * @param {Array} alerts - 警报数据
         */
        updateAlerts(alerts) {
            if (!alerts || !Array.isArray(alerts)) {
                console.warn('没有警报数据可用');
                return;
            }
            
            const tableBody = document.querySelector('#alerts-table tbody');
            if (!tableBody) return;
            
            // 清空现有行
            tableBody.innerHTML = '';
            
            // 添加新的警报行
            alerts.forEach(alert => {
                const row = document.createElement('tr');
                row.dataset.alertId = alert[5] || '';
                row.innerHTML = `
                    <td>${alert[0] || ''}</td>
                    <td><span class="alert-type ${alert[1]?.toLowerCase() || ''}">${alert[1] || ''}</span></td>
                    <td>${alert[2] || ''}</td>
                    <td><span class="alert-status ${alert[3]?.toLowerCase() || ''}">${alert[3] || ''}</span></td>
                    <td><button class="btn btn-sm btn-primary">${alert[4] || '查看'}</button></td>
                `;
                
                tableBody.appendChild(row);
            });
            
            // 如果没有警报，显示空状态
            if (alerts.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = `
                    <td colspan="5" class="text-center">当前没有警报</td>
                `;
                tableBody.appendChild(emptyRow);
            }
            
            // 重新绑定事件
            this.bindAlertRowEvents();
        }

        /**
         * 导出仪表盘数据
         */
        exportDashboard() {
            try {
                // 创建包含日期范围的参数
                let exportUrl = `/api/dashboard/export_dashboard?date_range=${this.dateRange}&format=pdf`;
                
                // 添加自定义日期范围参数（如果有）
                if (this.dateRange === 'custom' && this.startDate && this.endDate) {
                    exportUrl += `&start_date=${this.startDate}&end_date=${this.endDate}`;
                }
                
                // 创建下载链接并点击
                const link = document.createElement('a');
                link.href = exportUrl;
                link.target = '_blank';
                link.download = `仪表盘数据_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                console.log('导出请求已发送:', exportUrl);
            } catch (error) {
                console.error('导出仪表盘数据时出错:', error);
                this.showError('导出失败，请重试');
            }
        }
    }

    // 创建并初始化仪表盘管理器
    const dashboard = new DashboardManager();
    dashboard.init();
    
    // 将实例暴露给全局作用域，以便其他脚本访问
    window.dashboardManager = dashboard;
})(); 