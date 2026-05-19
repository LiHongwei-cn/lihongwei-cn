const app = getApp();
const api = require('./api.js');

const DEV_FALLBACK = 'dev_preview_fallback';

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        const code = (res.code && res.code.length > 0) ? res.code : DEV_FALLBACK;
        doAuth(code, resolve, reject);
      },
      fail: () => {
        doAuth(DEV_FALLBACK, resolve, reject);
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
    .catch(reject);
}

module.exports = { login };
