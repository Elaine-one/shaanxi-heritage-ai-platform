/**
 * 旅游规划Agent前端集成模块
 * 负责初始化旅游规划Agent和集成其他模块
 */

window.submitPlanningConfig = function() {
    console.log('submitPlanningConfig函数被调用');
    if (window.travelAgent) {
        window.travelAgent.startTravelPlanning();
    } else {
        console.error('旅游规划Agent尚未初始化');
    }
};

document.addEventListener('DOMContentLoaded', async () => {
    try {
        if (window.travelAgent) {
            console.log('检测到旧的Agent实例，正在销毁...');
            if (typeof window.travelAgent.destroy === 'function') {
                window.travelAgent.destroy();
            }
            window.travelAgent = null;
        }
        
        window.travelAgent = new TravelPlanningAgent();
        console.log('旅游规划Agent实例化成功');
    } catch (error) {
        console.error('初始化旅游规划Agent失败:', error);
    }
});
