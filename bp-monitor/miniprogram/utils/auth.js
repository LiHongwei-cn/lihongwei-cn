var app = getApp();
var api = require('./api.js');

function login() {
  return new Promise(function (resolve, reject) {
    wx.login({
      success: function (res) {
        var code = (res.code && res.code.length > 0) ? res.code : '';
        if (code) {
          api.post('/auth/login', { code: code })
            .then(function (data) {
              app.globalData.token = data.token;
              app.globalData.userInfo = data.user;
              wx.setStorageSync('token', data.token);
              resolve(data.user);
            })
            .catch(function (err) {
              var hint = app.globalData.isDevtools
                ? '请确认后端已启动（localhost:8080）'
                : '请确认隧道服务正常运行';
              reject(new Error(hint + ' — ' + err.message));
            });
        } else {
          reject(new Error('微信登录未就绪，请在微信中重新打开小程序'));
        }
      },
      fail: function (err) {
        reject(new Error('登录失败: ' + (err.errMsg || '请重试')));
      }
    });
  });
}

module.exports = { login: login };
