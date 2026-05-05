(function() {
  var CACHE_KEY = 'maxkb_config_status';
  var CACHE_DURATION = 30 * 60 * 1000;

  var cached = null;
  try {
    var raw = localStorage.getItem(CACHE_KEY);
    if (raw) {
      var parsed = JSON.parse(raw);
      if (Date.now() - parsed.timestamp < CACHE_DURATION) {
        cached = parsed;
      } else {
        localStorage.removeItem(CACHE_KEY);
      }
    }
  } catch (e) {}

  if (cached && !cached.available) {
    console.warn('MaxKB配置不可用（缓存），跳过聊天机器人加载');
    return;
  }

  var getMaxKBConfig = async function() {
    try {
      var controller = new AbortController();
      var timeoutId = setTimeout(function() { controller.abort(); }, 3000);

      var response = await fetch('/api/third-party/config/maxkb/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        var config = await response.json();
        if (config && config.embed_url) {
          try {
            localStorage.setItem(CACHE_KEY, JSON.stringify({ available: true, timestamp: Date.now() }));
          } catch (e) {}
          return config;
        }
      }

      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ available: false, timestamp: Date.now() }));
      } catch (e) {}
      return null;
    } catch (error) {
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ available: false, timestamp: Date.now() }));
      } catch (e) {}
      return null;
    }
  };

  getMaxKBConfig().then(function(config) {
    if (config && config.embed_url) {
      var script = document.createElement('script');
      script.async = true;
      script.defer = true;
      script.src = config.embed_url;
      script.onerror = function() {
        console.warn('MaxKB聊天机器人加载失败');
      };
      document.head.appendChild(script);
    } else {
      console.warn('MaxKB配置不可用，跳过聊天机器人加载');
    }
  });
})();
