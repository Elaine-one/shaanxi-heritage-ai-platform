(function() {
    'use strict';

    window.notify = function(message, type) {
        type = type || 'info';
        if (typeof NotificationManager !== 'undefined' && NotificationManager[type]) {
            NotificationManager[type](message);
        } else {
            alert(message);
        }
    };

    window.requireLogin = async function(callback, promptMessage) {
        promptMessage = promptMessage || '请先登录';
        var isLoggedIn = false;
        if (typeof window.checkLoginStatus === 'function') {
            isLoggedIn = await window.checkLoginStatus();
        }
        if (!isLoggedIn) {
            if (typeof window.showLoginModal === 'function') {
                window.showLoginModal();
            } else {
                alert(promptMessage);
            }
            return;
        }
        return callback();
    };

    window.getFileType = function(file) {
        if (file.type.startsWith('video/')) return 'video';
        if (file.type.startsWith('image/')) return 'photo';
        if (file.type.startsWith('audio/')) return 'music';
        return 'article';
    };

    window.safeExecute = function(fn, fallbackValue) {
        try {
            return fn();
        } catch (e) {
            return fallbackValue !== undefined ? fallbackValue : null;
        }
    };
})();
