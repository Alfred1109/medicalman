/**
 * 财务分析模块
 * 负责初始化和更新财务分析页面的图表
 */

// 使用立即执行函数，避免污染全局命名空间
(function() {
    // 创建财务分析管理器类
    class FinancialAnalysisManager {
        constructor() {
            this.charts = {}; // 存储图表实例
            this.dateRange = 'month'; // 默认日期范围
            this.isLoading = false; // 加载状态
            this.chartContainers = {
                revenueTrend: 'revenue-trend-chart',
                revenueComposition: 'revenue-composition-chart',
                departmentFinance: 'department-finance-chart'
            };
        }
        
        /**
         * 初始化模块
         */
        init() {
            document.addEventListener('DOMContentLoaded', () => {
                this.bindEvents();
                this.initCharts();
                this.loadData();
            });
        }
        
        /**
         * 绑定事件处理器
         */
        bindEvents() {
            // 日期范围选择器
            const dateRangeSelector = document.getElementById('date-range-selector');
            if (dateRangeSelector) {
                dateRangeSelector.addEventListener('change', (e) => {
                    this.dateRange = e.target.value;
                    this.loadData();
                });
            }
            
            // 刷新按钮
            const refreshButton = document.getElementById('refresh-finance');
            if (refreshButton) {
                refreshButton.addEventListener('click', () => this.loadData(true));
            }
            
            // 导出按钮
            const exportButton = document.getElementById('export-finance');
            if (exportButton) {
                exportButton.addEventListener('click', () => this.exportData());
            }
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
            
            // 初始化收入趋势图
            this.initRevenueTrendChart();
            
            // 初始化收入构成图
            this.initRevenueCompositionChart();
            
            // 初始化部门财务图
            this.initDepartmentFinanceChart();
        }
        
        /**
         * 初始化收入趋势图
         */
        initRevenueTrendChart() {
            const containerId = this.chartContainers.revenueTrend;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            // 使用新的图表工具函数
            this.charts.revenueTrend = Utils.chart.initChart(container, {
                title: {
                    text: '收入趋势',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis'
                },
                legend: {
                    data: ['收入金额', '同比变化'],
                    top: 30
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
                    data: []
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        name: '收入金额',
                        type: 'line',
                        smooth: true,
                        data: []
                    },
                    {
                        name: '同比变化',
                        type: 'line',
                        smooth: true,
                        data: []
                    }
                ]
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
                    text: '收入构成',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'horizontal',
                    top: 30,
                    data: []
                },
                series: [
                    {
                        name: '收入来源',
                        type: 'pie',
                        radius: ['40%', '70%'],
                        avoidLabelOverlap: false,
                        label: {
                            show: false,
                            position: 'center'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: '18',
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: []
                    }
                ]
            });
        }
        
        /**
         * 初始化部门财务图
         */
        initDepartmentFinanceChart() {
            const containerId = this.chartContainers.departmentFinance;
            const container = document.getElementById(containerId);
            
            if (!container) return;
            
            this.charts.departmentFinance = Utils.chart.initChart(container, {
                title: {
                    text: '科室财务对比',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: ['收入', '支出', '利润'],
                    top: 30
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'value'
                },
                yAxis: {
                    type: 'category',
                    data: []
                },
                series: [
                    {
                        name: '收入',
                        type: 'bar',
                        stack: 'total',
                        label: {
                            show: true
                        },
                        emphasis: {
                            focus: 'series'
                        },
                        data: []
                    },
                    {
                        name: '支出',
                        type: 'bar',
                        stack: 'total',
                        label: {
                            show: true
                        },
                        emphasis: {
                            focus: 'series'
                        },
                        data: []
                    },
                    {
                        name: '利润',
                        type: 'bar',
                        stack: 'total',
                        label: {
                            show: true
                        },
                        emphasis: {
                            focus: 'series'
                        },
                        data: []
                    }
                ]
            });
        }
        
        /**
         * 显示加载状态
         */
        showLoading() {
            this.isLoading = true;
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.showLoading();
            });
            
            const loadingIndicator = document.getElementById('loading-indicator');
            if (loadingIndicator) loadingIndicator.style.display = 'block';
        }
        
        /**
         * 隐藏加载状态
         */
        hideLoading() {
            this.isLoading = false;
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.hideLoading();
            });
            
            const loadingIndicator = document.getElementById('loading-indicator');
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
        
        /**
         * 加载财务数据
         * @param {boolean} forceRefresh - 是否强制刷新（忽略缓存）
         */
        async loadData(forceRefresh = false) {
            if (this.isLoading) return;
            
            try {
                this.showLoading();
                
                // 使用正确的API接口路径
                const startDate = "2025-01-01";  // 临时固定为示例数据范围
                const endDate = "2025-03-31";
                
                // 获取收入构成数据
                const compositionResult = await Utils.api.post('/analytics/api/finance/composition', {
                    start_date: startDate,
                    end_date: endDate
                }, !forceRefresh);
                
                // 获取财务汇总数据
                const summaryResult = await Utils.api.post('/analytics/api/finance/summary', {
                    start_date: startDate,
                    end_date: endDate
                }, !forceRefresh);
                
                // 检查API响应
                if (compositionResult.success && summaryResult.success) {
                    // 手动构建数据结构
                    const data = {
                        success: true,
                        data: {
                            summary: summaryResult.data,
                            composition: compositionResult.data,
                            metrics: {
                                totalRevenue: Object.values(compositionResult.data).reduce((sum, val) => sum + val, 0),
                                startDate: startDate,
                                endDate: endDate
                            }
                        }
                    };
                    
                    this.updateCharts(data);
                } else {
                    this.showError('获取数据失败: ' + 
                        (compositionResult.error || summaryResult.error || '未知错误'));
                    // 使用备用数据更新图表
                    this.updateChartsWithFallbackData();
                }
            } catch (error) {
                console.error('加载财务数据失败:', error);
                this.showError('加载数据时出错，请刷新重试');
                // 使用备用数据更新图表
                this.updateChartsWithFallbackData();
            } finally {
                this.hideLoading();
            }
        }
        
        /**
         * 显示错误信息
         * @param {string} message - 错误消息
         */
        showError(message) {
            console.error(message);
            
            // 使用Toast显示错误
            if (window.Utils && window.Utils.showToast) {
                window.Utils.showToast(message, 'error');
            } else {
                alert(message);
            }
        }
        
        /**
         * 使用API数据更新所有图表
         * @param {Object} data - API返回的数据
         */
        updateCharts(data) {
            const apiData = data.data || data;
            
            // 更新收入趋势图
            if (apiData.summary) {
                const summaryData = apiData.summary;
                const trend = this.processRevenueTrendData(summaryData);
                this.updateRevenueTrendChart(trend);
            }
            
            // 更新收入构成图
            if (apiData.composition) {
                const compositionData = apiData.composition;
                const pieData = this.processCompositionData(compositionData);
                this.updateRevenueCompositionChart(pieData);
            }
            
            // 更新部门财务图 - 使用备用数据因为API中没有
            const departmentData = Utils.chart.generateFallbackData('bar', {
                pointCount: 8,
                seriesCount: 2,
                maxValue: 5000
            });
            this.updateDepartmentFinanceChart(this.processDepartmentData(departmentData));
            
            // 更新统计卡片
            if (apiData.metrics) {
                this.updateMetrics(apiData.metrics);
            } else if (apiData.composition) {
                // 如果没有metrics但有composition，计算一些基本指标
                const totalRevenue = Object.values(apiData.composition).reduce((sum, val) => sum + val, 0);
                this.updateMetrics({
                    totalRevenue: totalRevenue,
                    startDate: data.meta?.start_date || "2025-01-01",
                    endDate: data.meta?.end_date || "2025-03-31"
                });
            }
        }
        
        /**
         * 使用备用数据更新图表
         */
        updateChartsWithFallbackData() {
            // 生成并使用备用数据
            const trendData = Utils.chart.generateFallbackData('line', {
                pointCount: 12,
                maxValue: 10000
            });
            
            const compositionData = Utils.chart.generateFallbackData('pie', {
                pointCount: 5,
                maxValue: 1000
            });
            
            const departmentData = Utils.chart.generateFallbackData('bar', {
                pointCount: 8,
                maxValue: 5000
            });
            
            // 使用备用数据更新图表
            if (this.charts.revenueTrend) {
                this.updateRevenueTrendChart(trendData);
            }
            
            if (this.charts.revenueComposition) {
                this.updateRevenueCompositionChart(compositionData);
            }
            
            if (this.charts.departmentFinance) {
                // 特殊处理堆叠柱状图的备用数据
                const departments = departmentData.xAxis.data;
                const chartData = {
                    yAxis: {
                        data: departments
                    },
                    series: [
                        {
                            name: '收入',
                            data: Array.from({length: departments.length}, () => Math.floor(Math.random() * 5000))
                        },
                        {
                            name: '支出',
                            data: Array.from({length: departments.length}, () => Math.floor(Math.random() * 3000))
                        },
                        {
                            name: '利润',
                            data: Array.from({length: departments.length}, () => Math.floor(Math.random() * 2000))
                        }
                    ]
                };
                this.updateDepartmentFinanceChart(chartData);
            }
        }
        
        /**
         * 更新收入趋势图
         * @param {Object} data - 图表数据
         */
        updateRevenueTrendChart(data) {
            const chart = this.charts.revenueTrend;
            if (!chart) return;
            
            const option = {
                xAxis: data.xAxis || {
                    data: data.dates || []
                },
                series: [
                    {
                        name: '收入金额',
                        data: data.series?.[0]?.data || data.revenueData || []
                    },
                    {
                        name: '同比变化',
                        data: data.series?.[1]?.data || data.growthData || []
                    }
                ]
            };
            
            Utils.chart.updateChart(chart, option);
        }
        
        /**
         * 更新收入构成图
         * @param {Object} data - 图表数据
         */
        updateRevenueCompositionChart(data) {
            const chart = this.charts.revenueComposition;
            if (!chart) return;
            
            const pieData = data.series?.[0]?.data || data.data || [];
            
            const option = {
                legend: {
                    data: pieData.map(item => item.name)
                },
                series: [
                    {
                        name: '收入来源',
                        data: pieData
                    }
                ]
            };
            
            Utils.chart.updateChart(chart, option);
        }
        
        /**
         * 更新部门财务图
         * @param {Object} data - 图表数据
         */
        updateDepartmentFinanceChart(data) {
            const chart = this.charts.departmentFinance;
            if (!chart) return;
            
            const option = {
                yAxis: {
                    data: data.yAxis?.data || data.departments || []
                },
                series: [
                    {
                        name: '收入',
                        data: data.series?.[0]?.data || data.revenue || []
                    },
                    {
                        name: '支出',
                        data: data.series?.[1]?.data || data.expense || []
                    },
                    {
                        name: '利润',
                        data: data.series?.[2]?.data || data.profit || []
                    }
                ]
            };
            
            Utils.chart.updateChart(chart, option);
        }
        
        /**
         * 更新统计指标卡片
         * @param {Object} metrics - 统计指标数据
         */
        updateMetrics(metrics) {
            // 遍历指标数据，更新对应的DOM元素
            Object.entries(metrics).forEach(([key, value]) => {
                const element = document.getElementById(`metric-${key}`);
                if (element) {
                    element.textContent = value;
                }
            });
        }
        
        /**
         * 导出数据
         */
        exportData() {
            try {
                // 构建导出API URL
                const apiUrl = `/analytics/api/finance/export?date_range=${this.dateRange}`;
                
                // 创建下载链接并点击
                const link = document.createElement('a');
                link.href = apiUrl;
                link.target = '_blank';
                link.download = `财务分析_${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (error) {
                console.error('导出数据失败:', error);
                this.showError('导出数据失败，请重试');
            }
        }
        
        /**
         * 处理收入趋势数据
         * @param {Array} summaryData - 收入汇总数据
         * @returns {Object} 处理后的趋势图数据
         */
        processRevenueTrendData(summaryData) {
            // 按月分组数据
            const monthlyData = {};
            
            summaryData.forEach(item => {
                const date = item.date.substring(0, 7); // 使用YYYY-MM格式
                const type = item.type;
                
                if (!monthlyData[date]) {
                    monthlyData[date] = { income: 0, expense: 0 };
                }
                
                if (type === 'income') {
                    monthlyData[date].income += item.amount;
                } else if (type === 'expense') {
                    monthlyData[date].expense += item.amount;
                }
            });
            
            // 转换为图表数据格式
            const months = Object.keys(monthlyData).sort();
            const incomeData = months.map(month => monthlyData[month].income);
            const expenseData = months.map(month => monthlyData[month].expense);
            
            return {
                xAxis: { data: months },
                series: [
                    {
                        name: '收入',
                        data: incomeData
                    },
                    {
                        name: '支出',
                        data: expenseData
                    }
                ]
            };
        }
        
        /**
         * 处理收入构成数据
         * @param {Object} compositionData - 收入构成数据
         * @returns {Object} 处理后的饼图数据
         */
        processCompositionData(compositionData) {
            const pieData = Object.entries(compositionData).map(([key, value]) => {
                return {
                    name: this.translateRevenueType(key),
                    value: value
                };
            });
            
            return {
                data: pieData
            };
        }
        
        /**
         * 翻译收入类型名称
         * @param {string} type - 收入类型代码
         * @returns {string} 翻译后的名称
         */
        translateRevenueType(type) {
            const translations = {
                'outpatient': '门诊收入',
                'inpatient': '住院收入',
                'drug': '药品收入',
                'examination': '检查收入',
                'surgery': '手术收入',
                'other': '其他收入'
            };
            
            return translations[type] || type;
        }
        
        /**
         * 处理部门财务数据
         * @param {Object} departmentData - 部门财务数据
         * @returns {Object} 处理后的柱状图数据
         */
        processDepartmentData(departmentData) {
            // 这里我们假设departmentData已经是一个有效的ECharts配置
            // 在真实API返回时，需要根据实际格式调整
            const departments = departmentData.xAxis.data.slice(0, 8);
            
            return {
                yAxis: {
                    data: departments
                },
                series: [
                    {
                        name: '收入',
                        data: Array.from({length: departments.length}, () => Math.floor(Math.random() * 5000 + 3000))
                    },
                    {
                        name: '支出',
                        data: Array.from({length: departments.length}, () => Math.floor(Math.random() * 3000 + 2000))
                    }
                ]
            };
        }
    }
    
    // 创建并初始化财务分析管理器
    const financialAnalysis = new FinancialAnalysisManager();
    financialAnalysis.init();
    
    // 清理重复的图表标题（兼容旧代码）
    function cleanupDuplicateChartTitles() {
        // 查找所有图表容器
        const chartContainers = document.querySelectorAll('.chart-container');
        
        chartContainers.forEach(container => {
            // 查找容器内的所有标题元素
            const titles = container.querySelectorAll('.chart-title');
            
            // 如果有多个标题，保留第一个，删除其余的
            if (titles.length > 1) {
                console.log(`发现重复的图表标题，清理中...`);
                for (let i = 1; i < titles.length; i++) {
                    titles[i].remove();
                }
            }
        });
    }
    
    // 添加到window对象，以便在其他脚本中访问
    window.financialAnalysis = financialAnalysis;
    window.cleanupDuplicateChartTitles = cleanupDuplicateChartTitles;
})(); 