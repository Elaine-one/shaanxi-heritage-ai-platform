// 动态加载Dify聊天机器人配置和脚本
(function() {
  // 通过后端API获取Dify配置
  const getDifyConfig = async () => {
    try {
      const response = await fetch('/api/third-party/config/dify/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        timeout: 3000
      });
      
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.warn('获取Dify配置失败:', error);
      return null;
    }
  };

  getDifyConfig().then(config => {
    if (config) {
      // 设置Dify配置
      window.difyChatbotConfig = {
        token: config.token,
        baseUrl: config.base_url,
        systemVariables: config.system_variables || {},
        ...config.additional_config
      };
      
      // 加载Dify聊天机器人脚本
      const script = document.createElement('script');
      script.src = config.base_url + '/embed.min.js';
      script.id = config.token;
      script.defer = true;
      document.head.appendChild(script);

      // 添加样式
      const style = document.createElement('style');
      style.textContent = `
        #dify-chatbot-bubble-button {
          background-color: #1C64F2 !important;
        }
        #dify-chatbot-bubble-window {
          width: 24rem !important;
          height: 40rem !important;
        }
      `;
      document.head.appendChild(style);
    } else {
      console.warn('Dify配置不可用，跳过聊天机器人加载');
    }
  });
})();