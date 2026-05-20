var app = getApp();
var api = require('./api.js');

function login() {
  return new Promise(function (resolve, reject) {
    wx.login({
      success: function (res) {
        var code = res.code || 'dev_dummy_code';
        doApiLogin(code, resolve, reject);
      },
      fail: function () {
        doApiLogin('dev_dummy_code', resolve, reject);
      }
    });
  });
}

function doApiLogin(code, resolve, reject) {
  api.post('/auth/login', { code: code })
    .then(function (data) {
      app.globalData.token = data.token;
      app.globalData.userInfo = data.user;
      wx.setStorageSync('token', data.token);
      resolve(data.user);
    })
    .catch(function (err) {
      var hint = app.globalData.isDevtools
        ? '请确认后端已启动且 BP_DEV_MODE=1'
        : '请确认后端服务正常运行';
      reject(new Error(hint + ' — ' + err.message));
    });
}

function logout() {
  app.clearLogin();
  wx.reLaunch({ url: '/pages/index/index' });
}

function checkDisclaimerAccepted() {
  var user = app.globalData.userInfo;
  return user && user.disclaimer_accepted === 1;
}

module.exports = { login: login, logout: logout, checkDisclaimerAccepted: checkDisclaimerAccepted };
