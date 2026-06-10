var app = getApp();
var api = require('./api.js');

function login() {
  return api.post('/auth/login', { code: '' }).then(function (data) {
    app.globalData.userInfo = data.user;
    return data.user;
  }).catch(function (err) {
    var msg = err.message || '登录失败';
    if (msg.indexOf('cloud function') !== -1) {
      msg = '云函数调用失败，请检查：\n' +
        '1. 微信开发者工具中已开通云开发\n' +
        '2. 云函数已上传部署\n' +
        '3. app.js 中 env 参数已替换为你的云环境 ID\n\n' +
        '原始错误：' + msg;
    }
    throw new Error(msg);
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
