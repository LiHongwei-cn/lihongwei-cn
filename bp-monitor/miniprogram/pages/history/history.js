const api = require('../../utils/api.js');

Page({
  data: {
    filterDays: 7,
    readings: [],
    page: 1,
    hasMore: false,
    expandedId: null
  },

  onShow() { this.loadReadings(); },

  setFilter(e) {
    const days = parseInt(e.currentTarget.dataset.days);
    this.setData({ filterDays: days, page: 1, readings: [] });
    this.loadReadings();
  },

  loadReadings() {
    const { filterDays, page } = this.data;
    const endDate = new Date().toISOString().split('T')[0];
    const start = new Date();
    start.setDate(start.getDate() - filterDays);
    const startDate = start.toISOString().split('T')[0];

    api.get('/readings', { page, limit: 20, start_date: startDate, end_date: endDate })
      .then((data) => {
        this.setData({
          readings: page === 1 ? data.items : [...this.data.readings, ...data.items],
          hasMore: data.has_more
        });
      }).catch(() => {});
  },

  loadMore() {
    const next = this.data.page + 1;
    this.setData({ page: next });
    this.loadReadings();
  },

  toggleAnalysis(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({
      expandedId: this.data.expandedId === id ? null : id
    });
  }
});
