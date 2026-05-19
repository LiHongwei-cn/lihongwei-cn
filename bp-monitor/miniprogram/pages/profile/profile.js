const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: {},
    age: '',
    genderIndex: 0,
    genderOptions: ['未选择', '男', '女'],
    diagnosisYear: '',
    yearOptions: [],
    targetSystolic: 140,
    targetDiastolic: 90,
    medications: [],
    timeOptions: ['morning', 'afternoon', 'evening', 'night'],
    timeLabels: { morning: '早晨', afternoon: '下午', evening: '晚上', night: '夜间' },
    loading: true
  },

  onShow() { this.loadProfile(); },

  loadProfile() {
    this.setData({ loading: true });
    api.get('/users/me').then((user) => {
      app.globalData.userInfo = user;
      let meds = [];
      try { meds = JSON.parse(user.medications || '[]'); } catch (e) { /* ignore */ }

      const years = [];
      const thisYear = new Date().getFullYear();
      for (let y = thisYear; y >= thisYear - 50; y--) years.push(String(y));

      const gi = user.gender === 'male' ? 1 : (user.gender === 'female' ? 2 : 0);

      this.setData({
        userInfo: user,
        age: user.age ? String(user.age) : '',
        genderIndex: gi,
        diagnosisYear: user.diagnosis_year ? String(user.diagnosis_year) : '',
        yearOptions: years,
        targetSystolic: user.target_systolic || 140,
        targetDiastolic: user.target_diastolic || 90,
        medications: meds
      });
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }).finally(() => {
      this.setData({ loading: false });
    });
  },

  onAgeInput(e) { this.setData({ age: e.detail.value }); },
  onTargetSysInput(e) { this.setData({ targetSystolic: e.detail.value }); },
  onTargetDiaInput(e) { this.setData({ targetDiastolic: e.detail.value }); },
  onGenderChange(e) { this.setData({ genderIndex: parseInt(e.detail.value) }); },
  onYearChange(e) {
    this.setData({ diagnosisYear: this.data.yearOptions[parseInt(e.detail.value)] });
  },

  addMed() {
    const meds = [...this.data.medications, { name: '', dose: '', time: 'morning' }];
    this.setData({ medications: meds });
  },

  onMedInput(e) {
    const { index, field } = e.currentTarget.dataset;
    const meds = this.data.medications.map((m, i) =>
      i === index ? { ...m, [field]: e.detail.value } : m
    );
    this.setData({ medications: meds });
  },

  onMedTimeChange(e) {
    const idx = e.currentTarget.dataset.index;
    const time = this.data.timeOptions[parseInt(e.detail.value)];
    const meds = this.data.medications.map((m, i) =>
      i === idx ? { ...m, time } : m
    );
    this.setData({ medications: meds });
  },

  delMed(e) {
    const idx = e.currentTarget.dataset.index;
    this.setData({ medications: this.data.medications.filter((_, i) => i !== idx) });
  },

  saveProfile() {
    const genderMap = ['', 'male', 'female'];
    api.put('/users/me', {
      age: this.data.age ? parseInt(this.data.age) : null,
      gender: genderMap[this.data.genderIndex] || '',
      diagnosis_year: this.data.diagnosisYear ? parseInt(this.data.diagnosisYear) : null,
      target_systolic: parseInt(this.data.targetSystolic) || 140,
      target_diastolic: parseInt(this.data.targetDiastolic) || 90,
      medications: JSON.stringify(this.data.medications)
    }).then(() => {
      wx.showToast({ title: '保存成功', icon: 'success' });
    }).catch(() => {
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
    });
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      success: (res) => {
        if (res.confirm) {
          app.clearLogin();
          wx.reLaunch({ url: '/pages/index/index' });
        }
      }
    });
  }
});
