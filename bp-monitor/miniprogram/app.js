App({
  globalData: {
    token: '',
    userInfo: null,

    // 开发模式：直连本地后端（需在微信开发者工具 → 详情 → 本地设置 → 勾选"不校验合法域名"）
    devApiBase: 'http://localhost:8080/api',

    // 生产隧道地址（由 tunnel_daemon.py 自动更新）
    tunnelApiBase: 'https://0c07147136f93f.lhr.life/api',

    // true = 开发模式连本地，false = 通过隧道连生产
    useDevServer: true,

    get apiBase() {
      return this.useDevServer ? this.devApiBase : this.tunnelApiBase;
    }
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
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
      success: (res) => {
        if (res.data && res.data.valid) {
          this.globalData.userInfo = res.data.user;
        } else {
          this.clearLogin();
        }
      },
      fail: () => {
        // token 校验失败不立即清除，可能是网络问题
        // 下次 onShow 会重新尝试
      }
    });
  },

  clearLogin() {
    this.globalData.token = '';
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
  }
});
