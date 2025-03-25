// 数据转换工具
const DataTransformer = {
    // 转换仪表盘数据
    transformDashboardData(response) {
        if (!response.success) {
            throw new Error(response.message || '数据获取失败');
        }

        const { metrics, charts, alerts } = response.data;
        
        return {
            stats: {
                outpatient: {
                    value: metrics.outpatient.count,
                    change: metrics.outpatient.change
                },
                inpatient: {
                    value: metrics.inpatient.count,
                    change: metrics.inpatient.change
                },
                revenue: {
                    value: `￥${metrics.revenue.amount}`,
                    change: metrics.revenue.change
                },
                bedUsage: {
                    value: `${metrics.bedUsage.rate}%`,
                    change: metrics.bedUsage.change
                }
            },
            charts: {
                outpatientTrend: this.transformOutpatientTrend(charts.outpatientTrend),
                revenueComposition: this.transformRevenueComposition(charts.revenueComposition),
                departmentWorkload: this.transformDepartmentWorkload(charts.departmentWorkload),
                inpatientDistribution: this.transformInpatientDistribution(charts.inpatientDistribution)
            },
            alerts: alerts.map(alert => ({
                time: alert.time,
                type: alert.type,
                description: alert.description,
                status: alert.status,
                action: alert.action
            }))
        };
    },

    // 转换门诊趋势数据
    transformOutpatientTrend(data) {
        return {
            xAxis: {
                data: data.dates
            },
            series: [
                {
                    name: '门诊量',
                    type: 'line',
                    data: data.values,
                    smooth: true
                },
                {
                    name: '同比',
                    type: 'line',
                    data: data.comparison,
                    smooth: true,
                    lineStyle: { type: 'dashed' }
                }
            ]
        };
    },

    // 转换收入构成数据
    transformRevenueComposition(data) {
        return {
            series: [{
                data: data.map(item => ({
                    name: item.name,
                    value: item.value
                }))
            }]
        };
    },

    // 转换科室工作量数据
    transformDepartmentWorkload(data) {
        return {
            yAxis: {
                data: data.departments
            },
            series: [
                {
                    name: '门诊量',
                    type: 'bar',
                    data: data.outpatient
                },
                {
                    name: '住院量',
                    type: 'bar',
                    data: data.inpatient
                }
            ]
        };
    },

    // 转换住院分布数据
    transformInpatientDistribution(data) {
        return {
            legend: {
                data: data.map(item => item.name)
            },
            series: [{
                data: data.map(item => ({
                    name: item.name,
                    value: item.value
                }))
            }]
        };
    }
}; 