const app = getApp();
const api = require('./api.js');

const DEV_FALLBACK_CODE = 'dev_preview_fallback';

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (loginRes) => {
        const code = (loginRes.code && loginRes.code.length > 0)
          ? loginRes.code
          : DEV_FALLBACK_CODE;
        doAuth(code, resolve, reject);
      },
      fail: () => {
        doAuth(DEV_FALLBACK_CODE, resolve, reject);
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
