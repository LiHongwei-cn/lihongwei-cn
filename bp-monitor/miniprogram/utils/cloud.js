/**
 * 云函数调用封装 - 统一错误处理与诊断
 */

function diagnoseError(err) {
  var errMsg = (err && err.errMsg) || '';
  var s = String(errMsg);

  if (s.indexOf('timeout') !== -1 || s.indexOf('TIMEOUT') !== -1) {
    return '请求超时，请检查网络连接';
  }
  if (s.indexOf('-501000') !== -1 || s.indexOf('Function not found') !== -1) {
    return '云函数未部署，请先上传云函数';
  }
  if (s.indexOf('not enable') !== -1 || s.indexOf('not enabled') !== -1) {
    return '云开发环境未开通，请在微信开发者工具中开通';
  }
  if (s.indexOf('-1') !== -1 || s.indexOf('system error') !== -1) {
    return '云开发服务异常（errCode: -1），请检查环境ID是否正确';
  }
  if (s.indexOf('offline') !== -1 || s.indexOf('network') !== -1) {
    return '网络连接失败，请检查手机网络';
  }
  // 兜底：显示原始错误码便于排查
  var codeHint = err && err.errCode ? ' [errCode: ' + err.errCode + ']' : '';
  return '云函数调用失败' + codeHint + '，请检查云开发配置';
}

function callFunction(action, data, opts) {
  opts = opts || {};
  return new Promise(function (resolve, reject) {
    wx.cloud.callFunction({
      name: 'api',
      data: { action: action, data: data || {} }
    }).then(function (res) {
      if (res.result && res.result.error) {
        reject(new Error(res.result.error));
        return;
      }
      resolve(res.result || {});
    }).catch(function (err) {
      var msg = diagnoseError(err);
      console.error('[cloud] callFunction ' + action + ' 失败:', err.errMsg || err.message, '→', msg);
      if (opts.silent !== true) {
        wx.showToast({ title: msg, icon: 'none', duration: 3000 });
      }
      reject(new Error(msg));
    });
  });
}

module.exports = {
  login:            function ()         { return callFunction('login'); },
  getUserProfile:   function ()         { return callFunction('getUserProfile'); },
  updateUserProfile:function (data)     { return callFunction('updateUserProfile', data); },
  addReading:       function (data)     { return callFunction('addReading', data); },
  getReadings:      function (data)     { return callFunction('getReadings', data); },
  getStats:         function (data)     { return callFunction('getStats', data); },
  generateReport:   function (data)     { return callFunction('generateReport', data); },
  getReports:       function ()         { return callFunction('getReports'); },
  deleteReading:    function (data)     { return callFunction('deleteReading', data); },
};
