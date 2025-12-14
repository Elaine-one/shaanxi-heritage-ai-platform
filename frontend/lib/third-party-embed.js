// 立即执行函数，确保API对象在全局范围内可用
(function(global) {
  console.log('初始化 API 对象...');
  
  // 确保全局API对象存在
  if (typeof global.API === 'undefined') {
    global.API = {};
  }
  
  // 确保heritage命名空间存在
  if (typeof global.API.heritage === 'undefined') {
    global.API.heritage = {};
  }
  
  // 定义API方法（如果尚未定义）
  if (!global.API.heritage.getAllItems) {
    global.API.heritage.getAllItems = async function() {
      console.warn('Mock API.heritage.getAllItems called from third-party-embed.js');
      return { results: [] };
    };
  }
  
  if (!global.API.heritage.getCategories) {
    global.API.heritage.getCategories = async function() {
      console.warn('Mock API.heritage.getCategories called from third-party-embed.js');
      return [
        { id: '1', name: '民间文学' },
        { id: '2', name: '传统音乐' },
        { id: '3', name: '传统舞蹈' }
      ];
    };
  }
  
  if (!global.API.heritage.getLevels) {
    global.API.heritage.getLevels = async function() {
      console.warn('Mock API.heritage.getLevels called from third-party-embed.js');
      return [
        { id: '国家级', name: '国家级' },
        { id: '省级', name: '省级' },
        { id: '市级', name: '市级' }
      ];
    };
  }
  
  if (!global.API.heritage.getRegions) {
    global.API.heritage.getRegions = async function() {
      console.warn('Mock API.heritage.getRegions called from third-party-embed.js');
      return [
        { id: '6101', name: '西安市' },
        { id: '6102', name: '铜川市' },
        { id: '6103', name: '宝鸡市' }
      ];
    };
  }
  
  console.log('third-party-embed.js 加载完成，API 对象状态:', global.API ? '已定义' : '未定义');
})(window);