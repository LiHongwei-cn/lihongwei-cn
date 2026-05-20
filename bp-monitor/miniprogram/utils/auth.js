var app = getApp();
var api = require('./api.js');

function login() {
  // 开发者工具环境：彻底跳过 wx.login()，直接调后端 dev 模式
  if (app.globalData.isDevtools) {
    return api.post('/auth/login', { code: 'dev_dummy_code' })
      .then(function (data) {
        app.globalData.token = data.token;
        app.globalData.userInfo = data.user;
        wx.setStorageSync('token', data.token);
        return data.user;
      })
      .catch(function (err) {
        throw new Error(
          '无法连接后端服务\n\n' +
          '请检查：\n' +
          '1. cd bp-monitor && bash deploy/start.sh 是否已启动\n' +
          '2. backend/.env 中 BP_DEV_MODE=1 是否已设置\n' +
          '3. 开发者工具 → 详情 → 不校验合法域名 是否已勾选\n\n' +
          '原始错误：' + (err.message || '未知错误')
        );
      });
  }

  // 真机环境：走微信标准登录流程
  return new Promise(function (resolve, reject) {
    wx.login({
      success: function (res) {
        var code = res.code || '';
        if (!code) {
          reject(new Error('微信登录未就绪，请在微信中重新打开小程序'));
          return;
        }
        doApiLogin(code, resolve, reject);
      },
      fail: function (err) {
        reject(new Error('微信登录失败: ' + (err.errMsg || '请重试')));
      }
    });
  });
}

function doApiLogin(code, resolve, reject) {
  api.post('/auth/login', { code: code })
    .then(function (data) {
      app.globalData.token = data.token;
      app.globalData.userInfo = data.user;
      wx.setStorageSync('token', data.token);
      resolve(data.user);
    })
    .catch(function (err) {
      reject(new Error('请确认后端服务正常运行 — ' + err.message));
    });
}

function logout() {
  app.clearLogin();
  wx.reLaunch({ url: '/pages/index/index' });
}

function checkDisclaimerAccepted() {
  var user = app.globalData.userInfo;
  return user && user.disclaimer_accepted === 1;
}

module.exports = { login: login, logout: logout, checkDisclaimerAccepted: checkDisclaimerAccepted };
