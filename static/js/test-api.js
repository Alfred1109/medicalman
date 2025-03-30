// API测试脚本
const testAPI = async () => {
  try {
    const response = await fetch("/api/dashboard/metrics", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({date_range: "week"})
    });
    const data = await response.json();
    console.log("API响应:", data);
    
    if(data && data.data && data.data.stats) {
      console.log("data.stats:", data.data.stats);
      if(data.data.stats.outpatient) {
        console.log("data.data.stats.outpatient:", data.data.stats.outpatient);
      } else {
        console.log("outpatient字段不存在");
      }
    } else {
      console.log("数据结构不完整，无法访问stats");
    }
  } catch(error) {
    console.error("API请求失败:", error);
  }
};

// 当页面加载完成时执行测试
window.addEventListener('DOMContentLoaded', () => {
  console.log("开始测试API...");
  testAPI();
}); 