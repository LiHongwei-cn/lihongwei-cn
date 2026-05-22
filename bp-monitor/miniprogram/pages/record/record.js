const cloud = require('../../utils/cloud.js');

const RANGES = {
  systolic: { min: 60, max: 300 },
  diastolic: { min: 30, max: 200 },
  heartRate: { min: 30, max: 250 }
};

Page({
  data: {
    systolic: '',
    diastolic: '',
    heartRate: '',
    timePeriod: '',
    notes: '',
    systolicError: '',
    diastolicError: '',
    heartRateError: '',
    submitting: false,
    analysis: ''
  },

  onLoad() {
    const hour = new Date().getHours();
    let period = 'morning';
    if (hour >= 10 && hour < 16) period = 'afternoon';
    else if (hour >= 16 && hour < 21) period = 'evening';
    else if (hour >= 21 || hour < 5) period = 'night';
    this.setData({ timePeriod: period });
  },

  onSystolicInput(e) { this.setData({ systolic: e.detail.value }); },
  onDiastolicInput(e) { this.setData({ diastolic: e.detail.value }); },
  onHeartRateInput(e) { this.setData({ heartRate: e.detail.value }); },
  onNotesInput(e) { this.setData({ notes: e.detail.value }); },

  validateField(val, range, label) {
    const v = parseInt(val);
    if (isNaN(v)) return '请输入数字';
    if (v < range.min || v > range.max) return label + '应在' + range.min + '-' + range.max + '之间';
    return '';
  },

  validateSys() {
    this.setData({ systolicError: this.validateField(this.data.systolic, RANGES.systolic, '收缩压') });
  },
  validateDia() {
    this.setData({ diastolicError: this.validateField(this.data.diastolic, RANGES.diastolic, '舒张压') });
  },
  validateHR() {
    const v = parseInt(this.data.heartRate);
    if (isNaN(v)) { this.setData({ heartRateError: '' }); return; }
    this.setData({ heartRateError: this.validateField(v, RANGES.heartRate, '心率') });
  },

  selectPeriod(e) {
    this.setData({ timePeriod: e.currentTarget.dataset.period });
  },

  submit() {
    const sys = parseInt(this.data.systolic);
    const dia = parseInt(this.data.diastolic);
    const hr = parseInt(this.data.heartRate);

    this.validateSys();
    this.validateDia();
    if (!isNaN(hr)) this.validateHR();

    if (this.data.systolicError || this.data.diastolicError || this.data.heartRateError) {
      wx.showToast({ title: '请修正输入错误', icon: 'none' });
      return;
    }

    if (isNaN(sys) || isNaN(dia)) {
      wx.showToast({ title: '请输入收缩压和舒张压', icon: 'none' });
      return;
    }

    if (sys > 200) {
      wx.showModal({
        title: '请确认',
        content: '收缩压为 ' + sys + ' mmHg，确认无误吗？',
        success: (res) => { if (res.confirm) this.doSubmit(); }
      });
      return;
    }

    this.doSubmit();
  },

  doSubmit() {
    const sys = parseInt(this.data.systolic);
    const dia = parseInt(this.data.diastolic);
    const hr = parseInt(this.data.heartRate);

    this.setData({ submitting: true, analysis: '' });

    cloud.addReading({
      systolic: sys,
      diastolic: dia,
      heartRate: isNaN(hr) ? null : hr,
      measuredAt: new Date().toISOString(),
      timePeriod: this.data.timePeriod,
      notes: this.data.notes
    }).then((data) => {
      this.setData({ submitting: false, analysis: (data.reading && data.reading.aiAnalysis) || '' });
      wx.showToast({ title: '记录成功', icon: 'success' });
      this.setData({ systolic: '', diastolic: '', heartRate: '', notes: '' });
    }).catch(() => {
      this.setData({ submitting: false });
    });
  }
});
