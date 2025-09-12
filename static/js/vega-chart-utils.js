/**
 * Vega-Lite 图表工具类
 * 提供统一的Vega-Lite图表管理和渲染功能
 */
const VegaChartUtils = {
    // 存储已注册的Vega-Lite视图
    vegaViews: {},
    
    /**
     * 注册Vega-Lite视图
     * @param {string} id - 视图ID
     * @param {Object} view - Vega视图实例
     */
    register: function(id, view) {
        if (!id || !view) return;
        
        // 如果已存在同ID视图，先清除
        if (this.vegaViews[id]) {
            this.vegaViews[id].finalize();
        }
        
        // 注册新视图
        this.vegaViews[id] = view;
        console.log(`Vega-Lite视图已注册: ${id}`);
    },
    
    /**
     * 获取已注册的Vega-Lite视图
     * @param {string} id - 视图ID
     * @returns {Object} Vega视图实例
     */
    get: function(id) {
        return this.vegaViews[id];
    },
    
    /**
     * 注销Vega-Lite视图
     * @param {string} id - 视图ID
     */
    unregister: function(id) {
        if (this.vegaViews[id]) {
            this.vegaViews[id].finalize();
            delete this.vegaViews[id];
            console.log(`Vega-Lite视图已注销: ${id}`);
        }
    },
    
    /**
     * 清除所有视图
     */
    destroyAll: function() {
        Object.keys(this.vegaViews).forEach(id => {
            this.unregister(id);
        });
        console.log('所有Vega-Lite视图已清除');
    },
    
    /**
     * 渲染单个Vega-Lite图表
     * @param {string|HTMLElement} container - 图表容器ID或DOM元素
     * @param {Object} spec - Vega-Lite规范
     * @param {Object} embedOptions - Vega-Embed选项
     * @returns {Promise} 返回Promise，resolve时包含视图实例
     */
    render: function(container, spec, embedOptions = {}) {
        return new Promise((resolve, reject) => {
            try {
                // 检查Vega-Embed是否可用
                if (typeof vegaEmbed === 'undefined') {
                    const error = new Error('Vega-Embed库未加载，无法渲染图表');
                    console.error(error.message);
                    reject(error);
                    return;
                }
                
                // 规范化容器参数
                let containerElement;
                if (typeof container === 'string') {
                    containerElement = document.getElementById(container);
                } else {
                    containerElement = container;
                }
                
                // 验证容器存在
                if (!containerElement) {
                    const error = new Error(`图表容器未找到: ${container}`);
                    console.error(error.message);
                    reject(error);
                    return;
                }
                
                // 确保容器有ID
                const containerId = containerElement.id || `vega-chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                if (!containerElement.id) {
                    containerElement.id = containerId;
                }
                
                // 清除可能存在的旧内容
                containerElement.innerHTML = '';
                
                // 确保规范有schema
                if (!spec.$schema) {
                    spec.$schema = "https://vega.github.io/schema/vega-lite/v5.json";
                }
                
                // 添加医疗主题配置
                if (!spec.config) {
                    spec.config = this.getMedicalThemeConfig();
                }
                
                // 默认嵌入选项
                const defaultOptions = {
                    theme: 'quartz',
                    tooltip: { 
                        theme: 'dark'
                    },
                    actions: {
                        export: true,
                        source: false,
                        compiled: false,
                        editor: false
                    }
                };
                
                const finalOptions = { ...defaultOptions, ...embedOptions };
                
                // 使用Vega-Embed渲染图表
                vegaEmbed(containerElement, spec, finalOptions)
                    .then(result => {
                        // 注册视图
                        this.register(containerId, result.view);
                        
                        console.log(`Vega-Lite图表 ${containerId} 渲染成功`);
                        resolve({
                            view: result.view,
                            spec: result.spec,
                            containerId: containerId
                        });
                    })
                    .catch(error => {
                        console.error(`Vega-Lite图表渲染失败:`, error);
                        
                        // 显示错误信息
                        containerElement.innerHTML = `
                            <div class="alert alert-warning" style="margin: 10px; padding: 15px; border-left: 4px solid #f0ad4e;">
                                <h6 style="margin-bottom: 5px;"><i class="fas fa-exclamation-triangle"></i> 图表渲染失败</h6>
                                <small style="color: #856404;">${error.message || '未知错误'}</small>
                            </div>
                        `;
                        
                        reject(error);
                    });
                
            } catch (error) {
                console.error('渲染Vega-Lite图表时发生异常:', error);
                reject(error);
            }
        });
    },
    
    /**
     * 获取医疗主题配置
     * @returns {Object} 医疗主题配置对象
     */
    getMedicalThemeConfig: function() {
        return {
            axis: {
                labelFontSize: 11,
                titleFontSize: 12,
                titleFontWeight: "bold",
                labelColor: "#666",
                titleColor: "#333"
            },
            title: {
                fontSize: 16,
                fontWeight: "bold",
                color: "#333",
                anchor: "start"
            },
            legend: {
                labelFontSize: 11,
                titleFontSize: 12,
                titleColor: "#333"
            },
            range: {
                category: [
                    "#4A90E2",  // 专业蓝
                    "#7ED321",  // 健康绿
                    "#F5A623",  // 温暖橙
                    "#D0021B",  // 警告红
                    "#9013FE",  // 科技紫
                    "#50E3C2",  // 清新青
                    "#B8E986",  // 自然绿
                    "#4A4A4A"   // 稳重灰
                ]
            }
        };
    },
    
    /**
     * 批量渲染多个图表
     * @param {Array} chartConfigs - 图表配置数组
     * @returns {Promise} 返回Promise，包含所有渲染结果
     */
    renderMultiple: function(chartConfigs) {
        if (!Array.isArray(chartConfigs)) {
            return Promise.reject(new Error('chartConfigs必须是数组'));
        }
        
        const renderPromises = chartConfigs.map((config, index) => {
            const { container, spec, embedOptions = {}, id } = config;
            const chartId = id || `chart-${index}`;
            
            return this.render(container, spec, embedOptions)
                .then(result => ({
                    success: true,
                    id: chartId,
                    containerId: result.containerId,
                    result: result
                }))
                .catch(error => ({
                    success: false,
                    id: chartId,
                    error: error
                }));
        });
        
        return Promise.all(renderPromises).then(results => {
            const summary = {
                total: results.length,
                success: results.filter(r => r.success).length,
                failed: results.filter(r => !r.success).length,
                results: results
            };
            
            console.log(`批量渲染Vega-Lite图表完成: 总数${summary.total}, 成功${summary.success}, 失败${summary.failed}`);
            return summary;
        });
    },
    
    /**
     * 更新图表数据
     * @param {string} viewId - 视图ID
     * @param {string} datasetName - 数据集名称，默认为'source_0'
     * @param {Array} newData - 新数据
     * @returns {boolean} 更新是否成功
     */
    updateData: function(viewId, datasetName = 'source_0', newData) {
        try {
            const view = this.vegaViews[viewId];
            if (!view) {
                console.warn(`未找到ID为${viewId}的Vega视图`);
                return false;
            }
            
            // 检查vega库是否可用
            if (typeof vega === 'undefined' || !vega.changeset) {
                console.warn('Vega库不可用，无法更新数据');
                return false;
            }
            
            // 创建changeset并更新数据
            const changeset = vega.changeset()
                .remove(() => true)  // 移除所有现有数据
                .insert(newData);    // 插入新数据
            
            view.change(datasetName, changeset).run();
            
            console.log(`Vega-Lite视图 ${viewId} 数据更新成功`);
            return true;
            
        } catch (error) {
            console.error(`更新Vega-Lite视图 ${viewId} 数据失败:`, error);
            return false;
        }
    },
    
    /**
     * 导出图表为图像
     * @param {string} viewId - 视图ID
     * @param {string} format - 导出格式 ('png', 'svg')
     * @param {number} scaleFactor - 缩放因子（仅PNG）
     * @returns {Promise} 返回Promise，resolve时包含图像URL或SVG字符串
     */
    exportChart: function(viewId, format = 'png', scaleFactor = 2) {
        return new Promise((resolve, reject) => {
            try {
                const view = this.vegaViews[viewId];
                if (!view) {
                    reject(new Error(`未找到ID为${viewId}的Vega视图`));
                    return;
                }
                
                if (format === 'png') {
                    view.toCanvas(scaleFactor).then(canvas => {
                        const dataURL = canvas.toDataURL('image/png');
                        resolve(dataURL);
                    }).catch(reject);
                } else if (format === 'svg') {
                    view.toSVG().then(svg => {
                        resolve(svg);
                    }).catch(reject);
                } else {
                    reject(new Error(`不支持的导出格式: ${format}`));
                }
            } catch (error) {
                reject(error);
            }
        });
    },
    
    /**
     * 获取图表的当前规范
     * @param {string} viewId - 视图ID
     * @returns {Object|null} 当前的Vega-Lite规范
     */
    getSpec: function(viewId) {
        try {
            const view = this.vegaViews[viewId];
            if (!view) {
                console.warn(`未找到ID为${viewId}的Vega视图`);
                return null;
            }
            
            return view.getState ? view.getState().spec : null;
        } catch (error) {
            console.error(`获取视图 ${viewId} 规范失败:`, error);
            return null;
        }
    }
};

// 向后兼容：将VegaChartUtils也设置为全局ChartUtils（如果没有定义的话）
if (typeof ChartUtils === 'undefined') {
    window.ChartUtils = VegaChartUtils;
}

// 暴露到全局
window.VegaChartUtils = VegaChartUtils;

// 页面卸载时清理所有视图
window.addEventListener('beforeunload', function() {
    VegaChartUtils.destroyAll();
});

console.log('VegaChartUtils已加载');
