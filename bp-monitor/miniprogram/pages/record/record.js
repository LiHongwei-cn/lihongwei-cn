const api = require('../../utils/api.js');

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
    analysisResult: ''
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

  validateSystolic() {
    const v = parseInt(this.data.systolic);
    const e = this.validateRange(v, RANGES.systolic, '收缩压');
    this.setData({ systolicError: e });
  },
  validateDiastolic() {
    const v = parseInt(this.data.diastolic);
    const e = this.validateRange(v, RANGES.diastolic, '舒张压');
    this.setData({ diastolicError: e });
  },
  validateHeartRate() {
    const v = parseInt(this.data.heartRate);
    if (isNaN(v)) { this.setData({ heartRateError: '' }); return; }
    const e = this.validateRange(v, RANGES.heartRate, '心率');
    this.setData({ heartRateError: e });
  },

  validateRange(val, range, label) {
    if (isNaN(val)) return '请输入数字';
    if (val < range.min || val > range.max) return `${label}应在${range.min}-${range.max}之间`;
    return '';
  },

  selectPeriod(e) {
    this.setData({ timePeriod: e.currentTarget.dataset.period });
  },

  submit() {
    const sys = parseInt(this.data.systolic);
    const dia = parseInt(this.data.diastolic);
    const hr = parseInt(this.data.heartRate);

    // 先触发失焦校验
    this.validateSystolic();
    this.validateDiastolic();
    if (!isNaN(hr)) this.validateHeartRate();

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
        content: `您输入的收缩压为 ${sys} mmHg，确认无误吗？`,
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

    this.setData({ submitting: true, analysisResult: '' });

    const now = new Date();
    const measuredAt = now.toISOString();

    api.post('/readings', {
      systolic: sys,
      diastolic: dia,
      heart_rate: isNaN(hr) ? null : hr,
      measured_at: measuredAt,
      time_period: this.data.timePeriod,
      notes: this.data.notes
    }).then((data) => {
      this.setData({ submitting: false, analysisResult: data.ai_analysis });
      wx.showToast({ title: '记录成功', icon: 'success' });

      // 清空表单
      this.setData({
        systolic: '', diastolic: '', heartRate: '', notes: ''
      });
    }).catch(() => {
      this.setData({ submitting: false });
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
    });
  }
});
