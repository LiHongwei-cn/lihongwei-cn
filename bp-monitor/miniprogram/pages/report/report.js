const api = require('../../utils/api.js');

function getMonday(d) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(date.setDate(diff));
}

function fmtDate(d) {
  return d.toISOString().split('T')[0];
}

Page({
  data: {
    weekOffset: 0,
    weekStart: '',
    weekEnd: '',
    report: null,
    generating: false,
    loading: true
  },

  onShow() {
    this.updateWeek();
    this.loadReport();
  },

  updateWeek() {
    const base = new Date();
    base.setDate(base.getDate() + this.data.weekOffset * 7);
    const mon = getMonday(base);
    const sun = new Date(mon);
    sun.setDate(sun.getDate() + 6);
    this.setData({ weekStart: fmtDate(mon), weekEnd: fmtDate(sun) });
  },

  loadReport() {
    this.setData({ loading: true });
    api.get('/reports').then((reports) => {
      const ws = this.data.weekStart;
      const match = (reports || []).find(r => r.week_start === ws);
      this.setData({ report: match || null });
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }).finally(() => {
      this.setData({ loading: false });
    });
  },

  prevWeek() {
    this.setData({ weekOffset: this.data.weekOffset - 1, report: null });
    this.updateWeek();
    this.loadReport();
  },

  nextWeek() {
    if (this.data.weekOffset >= 0) return;
    this.setData({ weekOffset: this.data.weekOffset + 1, report: null });
    this.updateWeek();
    this.loadReport();
  },

  generate() {
    this.setData({ generating: true });
    api.post('/reports/generate', {}).then((data) => {
      this.setData({ generating: false, report: data });
      wx.showToast({ title: '报告已生成', icon: 'success' });
    }).catch(() => {
      this.setData({ generating: false });
    });
  }
});
