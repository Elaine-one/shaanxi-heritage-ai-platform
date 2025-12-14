(function() {
  // 通过后端API获取MaxKB配置
  const getMaxKBConfig = async () => {
    try {
      const response = await fetch('/api/third-party/config/maxkb/', {
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
      console.warn('获取MaxKB配置失败:', error);
      return null;
    }
  };

  // 只有在获取配置成功时才加载脚本
  getMaxKBConfig().then(config => {
    if (config && config.embed_url) {
      const script = document.createElement('script');
      script.async = true;
      script.defer = true;
      script.src = config.embed_url;
      script.onerror = () => {
        console.warn('MaxKB聊天机器人加载失败');
      };
      document.head.appendChild(script);
    } else {
      console.warn('MaxKB配置不可用，跳过聊天机器人加载');
    }
  });
})();