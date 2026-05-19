const app = getApp();
const api = require('./api.js');

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        const code = (res.code && res.code.length > 0) ? res.code : null;
        if (code) {
          doAuth(code, resolve, reject);
        } else {
          // wx.login 返回了空 code（开发工具未登录微信账号时出现）
          reject(new Error('微信登录未就绪，请在开发者工具中登录微信账号，或确认后端 DEV_MODE=true'));
        }
      },
      fail: (err) => {
        reject(new Error('wx.login 调用失败: ' + (err.errMsg || '未知错误')));
      }
    });
  });
}

function doAuth(code, resolve, reject) {
  api.post('/auth/login', { code })
    .then((data) => {
      app.globalData.token = data.token;
      app.globalData.userInfo = data.user;
      wx.setStorageSync('token', data.token);
      resolve(data.user);
    })
    .catch((err) => {
      reject(new Error('登录请求失败，请确认后端服务已启动（' + err.message + '）'));
    });
}

module.exports = { login };
