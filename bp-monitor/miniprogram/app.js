App({
  globalData: {
    token: '',
    userInfo: null,

    // 运行环境（onLaunch 自动检测）
    isDevtools: false,

    // 开发工具直连本地后端
    devApiBase: 'http://localhost:8080/api',

    // 正式环境 — Render 云部署（稳定 HTTPS，可加入微信白名单）
    prodApiBase: 'https://bp-monitor-api.onrender.com/api',

    get apiBase() {
      return this.isDevtools ? this.devApiBase : this.prodApiBase;
    }
  },

  onLaunch() {
    var sys = wx.getSystemInfoSync();
    this.globalData.isDevtools = sys.platform === 'devtools';

    var token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      this.checkLogin();
    }
  },

  checkLogin() {
    if (!this.globalData.token) return;
    var app = this;
    wx.request({
      url: this.globalData.apiBase + '/auth/check',
      header: { Authorization: 'Bearer ' + this.globalData.token },
      success: function (res) {
        if (res.data && res.data.valid) {
          app.globalData.userInfo = res.data.user;
        } else {
          app.clearLogin();
        }
      },
      fail: function () {
        // 网络波动，不清除登录态，下次 onShow 重试
      }
    });
  },

  clearLogin() {
    this.globalData.token = '';
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
  }
});
