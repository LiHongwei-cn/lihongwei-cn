const TREND_MAP = {
  improving:         { icon: '✅', title: '趋势向好', desc: '收缩压较前段改善，继续保持' },
  worsening:         { icon: '⚠️', title: '需要关注', desc: '收缩压较前段升高，请留意' },
  stable:            { icon: '💙', title: '血压平稳', desc: '近期血压稳定，保持良好习惯' },
  insufficient_data: { icon: '📋', title: '数据不足', desc: '继续记录以获取趋势分析' }
};

const cloud = require('../../utils/cloud.js');
const auth = require('../../utils/auth.js');
const app = getApp();

Page({
  data: {
    greeting: '',
    todayDate: '',
    latestReading: null,
    stats: {},
    loading: true,
    loginError: ''
  },

  onShow() {
    this.setGreeting();
    if (!app.globalData.userInfo) {
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
    const display = name ? name + '，' + g : g;

    const d = now.toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    });

    this.setData({ greeting: display, todayDate: d });
  },

  doLogin() {
    this.setData({ loading: true, loginError: '' });
    auth.login().then(() => {
      this.setGreeting();
      this.loadData();
    }).catch((err) => {
      this.setData({
        loading: false,
        loginError: err.message || '登录失败，请重试'
      });
    });
  },

  retryLogin() {
    this.doLogin();
  },

  loadData() {
    this.setData({ loading: true });
    Promise.all([
      cloud.getReadings({ page: 1, limit: 1 }),
      cloud.getStats({ days: 7 })
    ]).then(([listRes, statsRes]) => {
      const trend = TREND_MAP[statsRes.trend_direction] || TREND_MAP.insufficient_data;
      this.setData({
        latestReading: (listRes.items && listRes.items[0]) || null,
        stats: Object.assign(statsRes, {
          trendIcon: trend.icon,
          trendTitle: trend.title,
          trendDesc: trend.desc
        })
      });
    }).catch(() => {
      wx.showToast({ title: '加载数据失败', icon: 'none' });
    }).finally(() => {
      this.setData({ loading: false });
    });
  },

  onDeleteReading(e) {
    var readingId = e.detail.readingId;
    var self = this;
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这条血压记录吗？',
      success: function (res) {
        if (res.confirm) {
          cloud.deleteReading({ readingId: readingId }).then(function () {
            wx.showToast({ title: '已删除', icon: 'success', duration: 1500 });
            self.setData({ latestReading: null });
            self.loadData();
          });
        }
      }
    });
  },

  goRecord() { wx.navigateTo({ url: '/pages/record/record' }); },
  goHistory() { wx.navigateTo({ url: '/pages/history/history' }); },
  goReport() { wx.navigateTo({ url: '/pages/report/report' }); },
  goProfile() { wx.navigateTo({ url: '/pages/profile/profile' }); }
});
