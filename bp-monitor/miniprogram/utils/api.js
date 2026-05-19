var app = getApp();

function request(url, options) {
  options = options || {};
  var token = app.globalData.token || wx.getStorageSync('token');

  return new Promise(function (resolve, reject) {
    function doRequest(apiUrl) {
      wx.request({
        url: apiUrl + url,
        method: options.method || 'GET',
        data: options.data || {},
        timeout: 10000,
        header: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        success: function (res) {
          if (res.statusCode === 401) {
            app.clearLogin();
            wx.reLaunch({ url: '/pages/index/index' });
            reject(new Error('登录已过期'));
            return;
          }
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            var msg = (res.data && res.data.detail) || '服务器繁忙';
            wx.showToast({ title: msg, icon: 'none', duration: 3000 });
            reject(new Error(msg));
          }
        },
        fail: function (err) {
          reject(err);
        }
      });
    }

    // 第一次尝试
    doRequest(app.globalData.apiBase).catch(function (err) {
      // 如果是真机且用了隧道 URL 失败，可能是 tunnel 断了
      // 等待 1 秒重试一次（排除瞬时网络波动）
      setTimeout(function () {
        doRequest(app.globalData.apiBase).catch(function (err2) {
          var msg = '网络连接失败';
          if (err2.errMsg && err2.errMsg.indexOf('timeout') !== -1) {
            msg = '请求超时，请检查网络或后端服务';
          }
          wx.showToast({ title: msg, icon: 'none', duration: 4000 });
          reject(new Error(msg));
        });
      }, 1000);
    });
  });
}

module.exports = {
  get: function (url, data) { return request(url, { method: 'GET', data: data }); },
  post: function (url, data) { return request(url, { method: 'POST', data: data }); },
  put: function (url, data) { return request(url, { method: 'PUT', data: data }); }
};
