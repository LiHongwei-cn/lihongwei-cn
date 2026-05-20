const ci = require('miniprogram-ci');
const path = require('path');
const fs = require('fs');

const PROJECT_PATH = path.resolve(__dirname, 'miniprogram');
const APPID = 'wx241f0c5210a2c1bf';
const PRIVATE_KEY_PATH = path.resolve(__dirname, 'private.key');

if (!fs.existsSync(PRIVATE_KEY_PATH)) {
  console.error('[错误] 缺少上传私钥文件: private.key');
  console.error('请从微信公众平台下载：设置 → 开发设置 → 小程序代码上传密钥');
  process.exit(1);
}

const project = new ci.Project({
  appid: APPID,
  type: 'miniProgram',
  projectPath: PROJECT_PATH,
  privateKeyPath: PRIVATE_KEY_PATH,
  ignores: ['node_modules/**/*'],
});

const version = process.argv[2] || `v${Date.now().toString(36)}`;
const desc = process.argv[3] || 'CI 自动上传';

(async () => {
  console.log(`[上传] 版本: ${version}  描述: ${desc}`);
  const result = await ci.upload({
    project,
    version,
    desc,
    setting: {
      es6: true,
      es7: true,
      minify: true,
      minifyJS: true,
      minifyWXML: true,
      minifyWXSS: true,
    },
    onProgressUpdate: (info) => {
      if (info.status === 'doing') {
        console.log(`  ${info.desc || ''}`);
      }
    },
  });
  console.log('[完成] 上传成功，请在微信公众平台设为体验版');
})();
