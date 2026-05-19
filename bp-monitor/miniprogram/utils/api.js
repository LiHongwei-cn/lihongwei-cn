const app = getApp();

function request(url, options = {}) {
  const token = app.globalData.token || wx.getStorageSync('token');

  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.apiBase + url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
        ...(options.header || {})
      },
      success: (res) => {
        if (res.statusCode === 401) {
          app.clearLogin();
          wx.reLaunch({ url: '/pages/index/index' });
          reject(new Error('登录已过期'));
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const msg = (res.data && res.data.detail) || '服务器繁忙，请稍后再试';
          wx.showToast({ title: msg, icon: 'none', duration: 3000 });
          reject(new Error(msg));
        }
      },
      fail: (err) => {
        const msg = err.errMsg && err.errMsg.includes('timeout')
          ? '请求超时，请重试'
          : '网络连接失败，请检查网络';
        wx.showToast({ title: msg, icon: 'none', duration: 3000 });
        reject(new Error(msg));
      }
    });
  });
}

module.exports = {
  get: (url, data) => request(url, { method: 'GET', data }),
  post: (url, data) => request(url, { method: 'POST', data }),
  put: (url, data) => request(url, { method: 'PUT', data })
};
