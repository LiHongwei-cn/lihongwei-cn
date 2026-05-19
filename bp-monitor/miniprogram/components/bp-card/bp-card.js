Component({
  properties: {
    systolic: { type: Number, value: 0 },
    diastolic: { type: Number, value: 0 },
    heartRate: { type: Number, value: null },
    measuredAt: { type: String, value: '' },
    timePeriod: { type: String, value: '' },
    bpLevel: { type: String, value: '' },
    notes: { type: String, value: '' },
    aiAnalysis: { type: String, value: '' },
    showAnalysis: { type: Boolean, value: false }
  },

  data: {
    levelClass: 'normal',
    periodLabel: '',
    displayTime: ''
  },

  observers: {
    'bpLevel, measuredAt, timePeriod': function () {
      this.updateDisplay();
    }
  },

  lifetimes: {
    attached() {
      this.updateDisplay();
    }
  },

  methods: {
    updateDisplay() {
      const level = this.data.bpLevel || '';
      let cls = 'normal';
      if (level.includes('3级') || level.includes('2级')) cls = 'high';
      else if (level.includes('1级') || level.includes('高值')) cls = 'elevated';

      const labels = { morning: '早晨', afternoon: '下午', evening: '晚上', night: '夜间' };
      const period = labels[this.data.timePeriod] || '';

      let display = this.data.measuredAt;
      if (display && display.includes('T')) {
        const parts = display.split('T');
        display = parts[0] + ' ' + (parts[1] || '').substring(0, 5);
      }

      this.setData({ levelClass: cls, periodLabel: period, displayTime: display });
    }
  }
});
