App({
  globalData: {
    token: '',
    userInfo: null,

    // 运行环境（onLaunch 自动检测）
    isDevtools: false,

    // 开发者工具直连本地后端
    devApiBase: 'http://localhost:8080/api',

    // 真机走隧道（由 tunnel_daemon.py 自动更新域名）
    tunnelApiBase: 'https://42aacead3b236f.lhr.life/api',

    get apiBase() {
      return this.isDevtools ? this.devApiBase : this.tunnelApiBase;
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
    wx.request({
      url: this.globalData.apiBase + '/auth/check',
      header: { Authorization: 'Bearer ' + this.globalData.token },
      success: function (res) {
        if (res.data && res.data.valid) {
          getApp().globalData.userInfo = res.data.user;
        } else {
          getApp().clearLogin();
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
