// 图表配置模板
const ChartConfigs = {
    // 基础配置
    base: {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        }
    },

    // 折线图配置
    line: {
        ...this.base,
        xAxis: {
            type: 'category',
            boundaryGap: false
        },
        yAxis: {
            type: 'value'
        }
    },

    // 柱状图配置
    bar: {
        ...this.base,
        xAxis: {
            type: 'value'
        },
        yAxis: {
            type: 'category'
        }
    },

    // 饼图配置
    pie: {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            right: 10,
            top: 'center'
        }
    },

    // 环形图配置
    donut: {
        ...this.pie,
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
            }
        }]
    }
}; 