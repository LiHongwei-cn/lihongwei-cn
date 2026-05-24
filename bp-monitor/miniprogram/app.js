const auth = require('./utils/auth.js');

App({
  globalData: {
    userInfo: null
  },

  onLaunch() {
    wx.cloud.init({ env: 'cloud1-0gixoepv2654fa53', traceUser: true });
    this.checkLogin();
  },

  checkLogin() {
    auth.login().catch(function () {});
  },

  clearLogin() {
    this.globalData.userInfo = null;
  }
});
