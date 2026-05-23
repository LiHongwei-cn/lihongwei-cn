App({
  globalData: {
    userInfo: null,
    isDevtools: false
  },

  onLaunch() {
    // 替换为你的云环境 ID（微信云开发控制台 → 设置 → 环境ID）
    wx.cloud.init({ env: 'cloud1-0gixoepv2654fa53', traceUser: true });

    const sys = wx.getSystemInfoSync();
    this.globalData.isDevtools = sys.platform === 'devtools';

    this.checkLogin();
  },

  checkLogin() {
    const api = require('./utils/api.js');
    api.post('/auth/login', { code: '' }).then(data => {
      this.globalData.userInfo = data.user;
    }).catch(() => {
      this.globalData.userInfo = null;
    });
  },

  clearLogin() {
    this.globalData.userInfo = null;
  }
});
