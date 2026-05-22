App({
  globalData: {
    userInfo: null,
    cloudReady: false
  },

  onLaunch() {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上版本的基础库以使用云开发');
      return;
    }
    wx.cloud.init({
      env: 'prod-0g1g5jq3e2a5e4f8',
      traceUser: true
    });
    this.globalData.cloudReady = true;
    this.checkLogin();
  },

  checkLogin() {
    var app = this;
    wx.cloud.callFunction({
      name: 'api',
      data: { action: 'login' }
    }).then(function (res) {
      if (res.result && res.result.user) {
        app.globalData.userInfo = res.result.user;
      }
    }).catch(function () {
      // 网络波动，下次 onShow 重试
    });
  },

  clearUser() {
    this.globalData.userInfo = null;
  }
});
