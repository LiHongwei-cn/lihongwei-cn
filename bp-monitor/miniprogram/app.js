App({
  globalData: {
    token: '',
    userInfo: null,
    apiBase: 'https://bdefdbebce12c5.lhr.life/api'
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
      fail: () => this.clearLogin()
    });
  },

  clearLogin() {
    this.globalData.token = '';
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
  }
});
