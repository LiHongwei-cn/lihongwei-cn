const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');
const app = getApp();

Page({
  data: {
    greeting: '',
    todayDate: '',
    latestReading: null,
    stats: {},
    loading: true
  },

  onShow() {
    this.setGreeting();
    if (!app.globalData.token) {
      this.doLogin();
    } else {
      this.loadData();
    }
  },

  setGreeting() {
    const now = new Date();
    const hour = now.getHours();
    let g = '您好';
    if (hour < 10) g = '早上好';
    else if (hour < 14) g = '中午好';
    else if (hour < 18) g = '下午好';
    else g = '晚上好';

    const name = (app.globalData.userInfo && app.globalData.userInfo.nickname) || '';
    const display = name ? `${name}，${g}` : g;

    const d = now.toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    });

    this.setData({ greeting: display, todayDate: d });
  },

  doLogin() {
    auth.login().then(() => {
      this.setGreeting();
      this.loadData();
    }).catch(() => {
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    });
  },

  loadData() {
    this.setData({ loading: true });
    Promise.all([
      api.get('/readings', { page: 1, limit: 1 }),
      api.get('/readings/stats', { days: 7 })
    ]).then(([listRes, statsRes]) => {
      this.setData({
        latestReading: (listRes.items && listRes.items[0]) || null,
        stats: statsRes
      });
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }).finally(() => {
      this.setData({ loading: false });
    });
  },

  goRecord() { wx.navigateTo({ url: '/pages/record/record' }); },
  goHistory() { wx.navigateTo({ url: '/pages/history/history' }); },
  goReport() { wx.navigateTo({ url: '/pages/report/report' }); },
  goProfile() { wx.navigateTo({ url: '/pages/profile/profile' }); }
});
