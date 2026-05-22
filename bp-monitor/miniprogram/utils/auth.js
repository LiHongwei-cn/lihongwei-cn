var app = getApp();
var cloud = require('./cloud.js');

function login() {
  return cloud.login().then(function (data) {
    app.globalData.userInfo = data.user;
    return data.user;
  }).catch(function (err) {
    throw new Error('登录失败: ' + (err.message || '请检查网络连接'));
  });
}

function logout() {
  app.clearUser();
  wx.reLaunch({ url: '/pages/index/index' });
}

function checkDisclaimerAccepted() {
  var user = app.globalData.userInfo;
  return user && user.disclaimerAccepted === 1;
}

module.exports = { login: login, logout: logout, checkDisclaimerAccepted: checkDisclaimerAccepted };
