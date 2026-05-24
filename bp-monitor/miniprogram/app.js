const auth = require('./utils/auth.js');

App({
  globalData: {
    userInfo: null,
    loginPromise: null
  },

  onLaunch() {
    wx.cloud.init({ env: 'cloud1-d1gh87tb74f34ecb9', traceUser: true });
    this.preLogin();
  },

  preLogin() {
    this.globalData.loginPromise = auth.login().catch(function (err) {
      console.warn('[app] pre-login failed:', err.message);
    });
  },

  clearLogin() {
    this.globalData.userInfo = null;
    this.globalData.loginPromise = null;
  }
});
