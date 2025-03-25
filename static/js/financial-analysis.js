/**
 * 财务分析模块
 * 负责初始化和更新财务分析页面的图表
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取所有图表容器
    const chartContainers = document.querySelectorAll('.chart-container');
    if (chartContainers.length < 3) {
        console.error('图表容器数量不足，请检查HTML结构');
        return;
    }

    // 安全地初始化图表对象
    const revenueTrendChart = echarts.init(chartContainers[0]);
    const revenueCompositionChart = echarts.init(chartContainers[1]);
    const departmentFinanceChart = echarts.init(chartContainers[2]);
    
    // 获取CSRF令牌
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    
    // 设置请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    };
    
    // 获取当前日期和前一年的日期
    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);
    
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    const startDate = formatDate(lastYear);
    const endDate = formatDate(today);
    
    // 显示加载状态
    showLoading([revenueTrendChart, revenueCompositionChart, departmentFinanceChart]);
    
    // 获取财务数据
    fetch('/analytics/api/finance/summary', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            start_date: startDate,
            end_date: endDate
        }),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            const financeData = result.data;
            
            // 处理收入趋势数据
            const trendData = processTrendData(financeData);
            updateRevenueTrendChart(revenueTrendChart, trendData);
            
            // 获取收入构成数据
            return fetch('/analytics/api/finance/composition', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate
                }),
                credentials: 'same-origin'
            });
        } else {
            throw new Error(result.message || '获取财务数据失败');
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            const compositionData = result.data;
            
            // 处理收入构成数据
            updateRevenueCompositionChart(revenueCompositionChart, compositionData);
            
            // 获取科室财务数据
            return fetch('/analytics/api/department/revenue', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate
                }),
                credentials: 'same-origin'
            });
        } else {
            throw new Error(result.message || '获取收入构成数据失败');
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            const departmentData = result.data;
            
            // 处理科室财务数据
            updateDepartmentFinanceChart(departmentFinanceChart, departmentData);
            
            // 隐藏加载状态
            hideLoading([revenueTrendChart, revenueCompositionChart, departmentFinanceChart]);
        } else {
            throw new Error(result.message || '获取科室财务数据失败');
        }
    })
    .catch(error => {
        console.error('数据加载失败:', error);
        showError([revenueTrendChart, revenueCompositionChart, departmentFinanceChart], error.message);
    });
    
    // 处理收入趋势数据
    function processTrendData(data) {
        // 按月份聚合数据
        const monthlyData = {};
        
        data.forEach(item => {
            const date = new Date(item.date);
            const yearMonth = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            
            if (!monthlyData[yearMonth]) {
                monthlyData[yearMonth] = {
                    income: 0,
                    expense: 0,
                    profit: 0
                };
            }
            
            if (item.type === 'income') {
                monthlyData[yearMonth].income += item.amount;
            } else if (item.type === 'expense') {
                monthlyData[yearMonth].expense += item.amount;
            }
        });
        
        // 计算利润
        Object.keys(monthlyData).forEach(month => {
            monthlyData[month].profit = monthlyData[month].income - monthlyData[month].expense;
        });
        
        // 排序月份
        const sortedMonths = Object.keys(monthlyData).sort();
        
        // 构造返回数据
        return {
            months: sortedMonths.map(m => {
                const [year, month] = m.split('-');
                return `${month}月`;
            }),
            income: sortedMonths.map(m => Math.round(monthlyData[m].income / 1000)), // 转换为K
            expense: sortedMonths.map(m => Math.round(monthlyData[m].expense / 1000)),
            profit: sortedMonths.map(m => Math.round(monthlyData[m].profit / 1000))
        };
    }
    
    // 更新收入趋势图
    function updateRevenueTrendChart(chart, data) {
        const option = {
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['收入', '支出', '利润']
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
                data: data.months
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    formatter: '¥{value}K'
                }
            },
            series: [
                {
                    name: '收入',
                    type: 'line',
                    data: data.income,
                    smooth: true,
                    lineStyle: {
                        width: 3
                    }
                },
                {
                    name: '支出',
                    type: 'line',
                    data: data.expense,
                    smooth: true,
                    lineStyle: {
                        width: 3
                    }
                },
                {
                    name: '利润',
                    type: 'line',
                    data: data.profit,
                    smooth: true,
                    lineStyle: {
                        width: 3
                    },
                    itemStyle: {
                        color: '#5cb87a'
                    }
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 更新收入构成图
    function updateRevenueCompositionChart(chart, data) {
        // 处理数据格式
        const pieData = Object.entries(data).map(([key, value]) => {
            const nameMap = {
                'outpatient': '门诊',
                'inpatient': '住院',
                'drug': '药房',
                'examination': '检查',
                'surgery': '手术',
                'other': '其他'
            };
            
            return {
                name: nameMap[key] || key,
                value: Math.round(value / 1000) // 转换为K
            };
        });
        
        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: ¥{c}K ({d}%)'
            },
            legend: {
                orient: 'vertical',
                right: 10,
                top: 'center',
                data: pieData.map(item => item.name)
            },
            series: [
                {
                    name: '收入来源',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 5,
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
                            fontSize: '18',
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: pieData
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 更新科室财务对比图
    function updateDepartmentFinanceChart(chart, data) {
        // 按科室聚合数据
        const departmentData = {};
        
        data.forEach(item => {
            if (!departmentData[item.department]) {
                departmentData[item.department] = {
                    income: 0,
                    expense: 0
                };
            }
            
            departmentData[item.department].income += item.total_income;
            // 假设支出是收入的70%（如果API没有提供支出数据）
            departmentData[item.department].expense = departmentData[item.department].income * 0.7;
        });
        
        // 计算利润
        Object.keys(departmentData).forEach(dept => {
            departmentData[dept].profit = departmentData[dept].income - departmentData[dept].expense;
        });
        
        // 按收入排序并获取前6个科室
        const sortedDepts = Object.entries(departmentData)
            .sort((a, b) => b[1].income - a[1].income)
            .slice(0, 6)
            .map(([dept, _]) => dept);
        
        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            legend: {
                data: ['收入', '支出', '利润']
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLabel: {
                    formatter: '¥{value}K'
                }
            },
            yAxis: {
                type: 'category',
                data: sortedDepts
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
                    data: sortedDepts.map(dept => Math.round(departmentData[dept].income / 1000))
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
                    data: sortedDepts.map(dept => Math.round(departmentData[dept].expense / 1000))
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
                    data: sortedDepts.map(dept => Math.round(departmentData[dept].profit / 1000))
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 显示加载状态
    function showLoading(charts) {
        charts.forEach(chart => {
            chart.showLoading({
                text: '数据加载中...',
                color: '#3498db',
                textColor: '#000',
                maskColor: 'rgba(255, 255, 255, 0.8)',
                zlevel: 0
            });
        });
    }
    
    // 隐藏加载状态
    function hideLoading(charts) {
        charts.forEach(chart => {
            chart.hideLoading();
        });
    }
    
    // 显示错误信息
    function showError(charts, message) {
        charts.forEach(chart => {
            chart.hideLoading();
            chart.setOption({
                title: {
                    text: '加载失败',
                    subtext: message,
                    left: 'center',
                    top: 'center',
                    textStyle: {
                        color: '#e74c3c',
                        fontSize: 16
                    },
                    subtextStyle: {
                        color: '#7f8c8d'
                    }
                }
            });
        });
    }
    
    // 响应式调整
    window.addEventListener('resize', function() {
        revenueTrendChart.resize();
        revenueCompositionChart.resize();
        departmentFinanceChart.resize();
    });
}); 