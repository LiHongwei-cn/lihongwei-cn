const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const _ = db.command;

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const MAX_REANALYZE_PER_DAY = 5;

const SYSTEM_PROMPT = `## 身份
你是一位专业的高血压健康管理助手。你的知识基于全球四大权威高血压指南：
WHO/ISH、ACC/AHA、ESC/ESH、《中国高血压防治指南》。

你为高血压患者及其家属提供血压解读、趋势分析和生活方式建议。

## 血压分级标准（单位 mmHg）
| 分类 | 收缩压 | 舒张压 |
|------|--------|--------|
| 理想血压 | <120 | 且 <80 |
| 正常血压 | 120-129 | 且/或 80-84 |
| 正常高值 | 130-139 | 且/或 85-89 |
| 1级高血压 | 140-159 | 且/或 90-99 |
| 2级高血压 | 160-179 | 且/或 100-109 |
| 3级高血压 | >=180 | 且/或 >=110 |

## 安全红线
1. 绝不建议用户自行停药、换药或调整药物剂量
2. 绝不替代执业医师的诊断和处方
3. 遇到紧急指征必须立即建议就医
4. 不传播未经循证医学验证的偏方或保健品
5. 默认使用中文回复`;

const MEDICAL_DISCLAIMER = '\n---\n*以上分析由AI生成，仅供参考，不构成医疗诊断或处方。*';

async function callDeepSeek(messages) {
  if (!DEEPSEEK_API_KEY) return 'AI分析服务未配置。您的血压数据已安全保存。';
  try {
    const https = require('https');
    const body = JSON.stringify({ model: 'deepseek-v4-pro', messages });
    const result = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: 'api.deepseek.com',
        path: '/v1/chat/completions',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
        },
        timeout: 50000
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
        });
      });
      req.on('error', reject);
      req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
      req.write(body);
      req.end();
    });
    return result.choices?.[0]?.message?.content || 'AI分析返回为空';
  } catch (e) {
    console.error('DeepSeek error:', e);
    return 'AI分析暂时不可用，请稍后再试。';
  }
}

exports.main = async (event) => {
  const { OPENID } = cloud.getWXContext();
  if (!OPENID) return { errCode: 401, errMsg: '请先登录' };

  if (event.action !== 'analyze') return { errCode: 400, errMsg: '未知操作' };

  const readingId = event.readingId;
  if (!readingId) return { errCode: 400, errMsg: '缺少记录ID' };

  // Rate limit
  const today = new Date().toISOString().split('T')[0];
  const { total } = await db.collection('ai_feedback')
    .where({ userId: OPENID, promptType: 'reading_analysis', createdAt: _.gte(today) }).count();
  if (total >= MAX_REANALYZE_PER_DAY) {
    return { errCode: 429, errMsg: '今日重新分析次数已达上限' };
  }

  // Get reading
  let reading;
  try {
    const { data } = await db.collection('readings').doc(readingId).get();
    if (!data || data.userId !== OPENID) return { errCode: 404, errMsg: '未找到该记录' };
    reading = data;
  } catch {
    return { errCode: 404, errMsg: '未找到该记录' };
  }

  // Get user
  const { data: users } = await db.collection('users').where({ openid: OPENID }).get();
  const user = users.length > 0 ? users[0] : {};

  // Get recent readings
  const { data: recent } = await db.collection('readings')
    .where({ userId: OPENID, _id: _.neq(readingId) })
    .orderBy('measuredAt', 'desc')
    .limit(7)
    .get();

  let recentText = '（暂无历史记录）';
  if (recent.length > 0) {
    recentText = recent.reverse().map(r =>
      `- ${r.measuredAt}（${r.timePeriod || '未指定'}）：${r.systolic}/${r.diastolic}`
    ).join('\n');
  }

  const prompt = `请分析以下血压读数：

**本次读数**
- 收缩压：${reading.systolic} mmHg
- 舒张压：${reading.diastolic} mmHg
- 心率：${reading.heartRate || '未记录'} bpm
- 测量时间：${reading.measuredAt}

**用户信息**
- 年龄：${user.age || '未填写'}岁
- 目标血压：${user.targetSystolic || 140}/${user.targetDiastolic || 90} mmHg

**最近历史读数**
${recentText}

请按照以下格式回复：
📊 **本次读数分析**
💊 **用药提醒**
🍽️ **生活方式建议**
⚠️ **注意事项**
${MEDICAL_DISCLAIMER}`;

  const analysis = await callDeepSeek([
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: prompt }
  ]);

  await db.collection('readings').doc(readingId).update({
    data: { aiAnalysis: analysis, updatedAt: db.serverDate() }
  });

  await db.collection('ai_feedback').add({
    data: {
      userId: OPENID,
      readingId,
      promptType: 'reading_analysis',
      promptText: 're-analysis prompt',
      responseText: analysis,
      createdAt: db.serverDate()
    }
  });

  return { errCode: 0, readingId, analysis, bpLevel: reading.bpLevel };
};
