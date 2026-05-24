const cloud = require('./cloud.js');

function login() {
  return cloud.login().then(function (data) {
    var app = getApp();
    app.globalData.userInfo = data.user;
    return data.user;
  });
}

function logout() {
  var app = getApp();
  app.globalData.userInfo = null;
  wx.reLaunch({ url: '/pages/index/index' });
}

function checkDisclaimerAccepted() {
  var app = getApp();
  var user = app.globalData.userInfo;
  return user && user.disclaimer_accepted === 1;
}

module.exports = { login: login, logout: logout, checkDisclaimerAccepted: checkDisclaimerAccepted };
