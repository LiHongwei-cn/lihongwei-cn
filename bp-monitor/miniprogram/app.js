App({
  globalData: {
    userInfo: null,
    cloudReady: false,
    cloudCheckDone: false,
    cloudDiag: ''
  },

  onLaunch() {
    if (!wx.cloud) {
      console.error('[app] 当前微信版本不支持云开发，请升级微信或使用 2.2.3 以上基础库');
      this.globalData.cloudDiag = '微信版本过低，不支持云开发';
      this.globalData.cloudCheckDone = true;
      return;
    }

    try {
      wx.cloud.init({
        env: 'cloud1-d1gh87tb74f34ecb9',
        traceUser: true
      });
      this.globalData.cloudReady = true;
      console.log('[app] 云开发初始化成功');
    } catch (e) {
      console.error('[app] 云开发初始化失败:', e);
      this.globalData.cloudDiag = '云开发初始化失败：' + (e.message || '未知错误');
      this.globalData.cloudCheckDone = true;
      return;
    }

    // 异步检测云函数连通性
    this.checkCloudConnectivity();
  },

  checkCloudConnectivity(retryCount) {
    var app = this;
    retryCount = retryCount || 0;
    wx.cloud.callFunction({
      name: 'api',
      data: { action: 'login' }
    }).then(function (res) {
      app.globalData.cloudCheckDone = true;
      if (res.result && res.result.user) {
        app.globalData.userInfo = res.result.user;
        console.log('[app] 云函数连通正常，已登录');
      } else if (res.result && res.result.error) {
        console.warn('[app] 云函数返回错误:', res.result.error);
        app.globalData.cloudDiag = res.result.error;
      }
    }).catch(function (err) {
      var errMsg = (err && err.errMsg) || '';
      // 超时且未超过重试次数，等冷启动完成后重试
      if (errMsg.indexOf('timeout') !== -1 && retryCount < 2) {
        console.log('[app] 云函数冷启动超时，3秒后重试...');
        setTimeout(function () { app.checkCloudConnectivity(retryCount + 1); }, 3000);
        return;
      }
      app.globalData.cloudCheckDone = true;
      console.error('[app] 云函数连通性检测失败:', errMsg);
      if (errMsg.indexOf('-501000') !== -1 || errMsg.indexOf('Function not found') !== -1) {
        app.globalData.cloudDiag = '云函数未部署，请在微信开发者工具中右键 cloudfunctions/api → 上传并部署';
      } else if (errMsg.indexOf('not enable') !== -1) {
        app.globalData.cloudDiag = '云开发环境未开通，请点击工具栏「云开发」按钮开通';
      } else {
        app.globalData.cloudDiag = '无法连接云开发服务，请检查网络和环境配置';
      }
    });
  },

  clearUser() {
    this.globalData.userInfo = null;
  }
});
