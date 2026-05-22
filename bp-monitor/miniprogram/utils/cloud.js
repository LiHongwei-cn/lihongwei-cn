function callFunction(action, data) {
  return new Promise(function (resolve, reject) {
    wx.cloud.callFunction({
      name: 'api',
      data: { action: action, data: data || {} }
    }).then(function (res) {
      if (res.result && res.result.error) {
        wx.showToast({ title: res.result.error, icon: 'none', duration: 3000 });
        reject(new Error(res.result.error));
        return;
      }
      resolve(res.result || {});
    }).catch(function (err) {
      var msg = '网络连接失败';
      if (err.errMsg && err.errMsg.indexOf('timeout') !== -1) {
        msg = '请求超时，请检查网络';
      }
      wx.showToast({ title: msg, icon: 'none', duration: 3000 });
      reject(new Error(msg));
    });
  });
}

module.exports = {
  login: function () { return callFunction('login'); },
  getUserProfile: function () { return callFunction('getUserProfile'); },
  updateUserProfile: function (data) { return callFunction('updateUserProfile', data); },
  addReading: function (data) { return callFunction('addReading', data); },
  getReadings: function (data) { return callFunction('getReadings', data); },
  getStats: function (data) { return callFunction('getStats', data); },
  generateReport: function (data) { return callFunction('generateReport', data); },
  getReports: function () { return callFunction('getReports'); },
  deleteReading: function (data) { return callFunction('deleteReading', data); }
};
