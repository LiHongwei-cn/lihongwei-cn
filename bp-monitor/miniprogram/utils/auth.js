const app = getApp();
const api = require('./api.js');

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (loginRes) => {
        if (!loginRes.code) {
          reject(new Error('微信登录失败'));
          return;
        }
        api.post('/auth/login', { code: loginRes.code })
          .then((data) => {
            app.globalData.token = data.token;
            app.globalData.userInfo = data.user;
            wx.setStorageSync('token', data.token);
            resolve(data.user);
          })
          .catch(reject);
      },
      fail: reject
    });
  });
}

function checkDisclaimerAccepted() {
  const user = app.globalData.userInfo;
  return user && user.disclaimer_accepted === 1;
}

module.exports = { login, checkDisclaimerAccepted };
