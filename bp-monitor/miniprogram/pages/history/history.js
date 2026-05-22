const cloud = require('../../utils/cloud.js');

Page({
  data: {
    filterDays: 7,
    readings: [],
    page: 1,
    hasMore: false,
    expandedId: null,
    loading: false
  },

  onShow() { this.reload(); },

  onPullDownRefresh() {
    this.reload().finally(() => wx.stopPullDownRefresh());
  },

  reload() {
    this.setData({ page: 1, readings: [] });
    return this.loadReadings();
  },

  setFilter(e) {
    const days = parseInt(e.currentTarget.dataset.days);
    this.setData({ filterDays: days, page: 1, readings: [] });
    this.loadReadings();
  },

  loadReadings() {
    this.setData({ loading: true });
    const { filterDays, page } = this.data;
    const endDate = new Date().toISOString().split('T')[0];
    const start = new Date();
    start.setDate(start.getDate() - filterDays);
    const startDate = start.toISOString().split('T')[0];

    return cloud.getReadings({ page, limit: 20, startDate, endDate })
      .then((data) => {
        this.setData({
          readings: page === 1 ? data.items : [...this.data.readings, ...data.items],
          hasMore: data.hasMore
        });
      }).catch(() => {
        wx.showToast({ title: '加载失败', icon: 'none' });
      }).finally(() => {
        this.setData({ loading: false });
      });
  },

  loadMore() {
    if (this.data.loading || !this.data.hasMore) return;
    const next = this.data.page + 1;
    this.setData({ page: next });
    this.loadReadings();
  },

  toggleAnalysis(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ expandedId: this.data.expandedId === id ? null : id });
  },

  onDeleteReading(e) {
    const readingId = e.detail.readingId;
    var self = this;
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这条血压记录吗？',
      success: function (res) {
        if (res.confirm) {
          cloud.deleteReading({ readingId: readingId }).then(function () {
            wx.showToast({ title: '已删除', icon: 'success', duration: 1500 });
            var readings = self.data.readings.filter(function (r) { return r._id !== readingId; });
            self.setData({ readings: readings });
          });
        }
      }
    });
  }
});
