/**
 * 旅游规划Agent前端集成模块
 * 负责初始化旅游规划Agent和集成其他模块
 */

// 旅游规划Agent主入口文件
// 引入其他模块并初始化旅游规划Agent

// 初始化全局submitPlanningConfig函数，供profile.html使用
window.submitPlanningConfig = function() {
    console.log('submitPlanningConfig函数被调用');
    if (window.travelAgent) {
        window.travelAgent.startTravelPlanning();
    } else {
        console.error('旅游规划Agent尚未初始化');
    }
};

// 等待DOM加载完成后初始化旅游规划Agent
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 初始化旅游规划Agent
        window.travelAgent = new TravelPlanningAgent();
        console.log('旅游规划Agent实例化成功');
    } catch (error) {
        console.error('初始化旅游规划Agent失败:', error);
    }
});
