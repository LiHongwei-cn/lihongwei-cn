const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const _ = db.command;

const MAX_READINGS_PER_DAY = 10;
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';

// ── BP Classification (ported from Python medical.py) ──

function classifyBp(systolic, diastolic) {
  if (systolic >= 180 || diastolic >= 110) return '3级高血压（重度）';
  if (systolic >= 160 || diastolic >= 100) return '2级高血压（中度）';
  if (systolic >= 140 || diastolic >= 90)  return '1级高血压（轻度）';
  if (systolic >= 130 || diastolic >= 85)  return '正常高值';
  if (systolic >= 120 || diastolic >= 80)  return '正常血压';
  return '理想血压';
}

function isEmergency(systolic, diastolic, notes) {
  if (systolic >= 180 || diastolic >= 110) {
    const keywords = ['头痛', '视力模糊', '胸闷', '呼吸困难', '头晕', '胸痛', '说不清话', '无力', '恶心'];
    if (keywords.some(k => (notes || '').includes(k))) return true;
  }
  if (systolic < 90) return true;
  return false;
}

function medicationSummary(medications) {
  if (!Array.isArray(medications) || medications.length === 0) return '未填写';
  return medications.map(m => {
    const name = m.name || '';
    const dose = m.dose || '';
    const time = m.time || '';
    return dose ? `${name} ${dose}（${time}）` : name;
  }).join('、');
}

// ── Prompt Templates ──

const SYSTEM_PROMPT = `## 身份
你是一位专业的高血压健康管理助手。你的知识基于全球四大权威高血压指南：
1. WHO/ISH《全球高血压防治指南》
2. ACC/AHA《美国心脏病学会/美国心脏协会高血压指南》
3. ESC/ESH《欧洲心脏病学会/欧洲高血压学会动脉高血压管理指南》
4. 《中国高血压防治指南》

你为高血压患者及其家属提供血压解读、趋势分析和生活方式建议。

## 血压分级标准（诊室血压，单位 mmHg）
| 分类 | 收缩压 | 舒张压 |
|------|--------|--------|
| 理想血压 | <120 | 且 <80 |
| 正常血压 | 120-129 | 且/或 80-84 |
| 正常高值 | 130-139 | 且/或 85-89 |
| 1级高血压（轻度） | 140-159 | 且/或 90-99 |
| 2级高血压（中度） | 160-179 | 且/或 100-109 |
| 3级高血压（重度） | >=180 | 且/或 >=110 |

## 治疗目标
- 一般高血压患者：<140/90 mmHg
- 65-79岁老年人：<140/90 mmHg（如能耐受）
- 80岁以上高龄老人：<150/90 mmHg
- 合并糖尿病/肾病/冠心病：<130/80 mmHg

## 安全红线
1. 绝不建议用户自行停药、换药或调整药物剂量
2. 绝不替代执业医师的诊断和处方
3. 遇到紧急指征必须立即建议就医
4. 不传播未经循证医学验证的偏方或保健品
5. 默认使用中文回复`;

const MEDICAL_DISCLAIMER = '\n---\n*以上分析由AI生成，仅供参考，不构成医疗诊断或处方。请以执业医师的诊断和治疗方案为准。如有不适，请及时就医。*';

const TIME_PERIOD_LABELS = {
  morning: '早晨（起床后1小时内）',
  afternoon: '下午',
  evening: '晚上（睡前1小时内）',
  night: '夜间'
};

function buildReadingPrompt(params) {
  const hrStr = params.heartRate ? String(params.heartRate) : '未记录';
  const tpLabel = TIME_PERIOD_LABELS[params.timePeriod] || (params.timePeriod || '未指定');
  const ageStr = params.age ? String(params.age) : '未填写';
  const genderStr = params.gender || '未填写';
  const diagStr = params.diagnosisYear ? String(params.diagnosisYear) : '未填写';
  const medsStr = params.medications && params.medications !== '未填写' ? params.medications : '未填写';

  return `请分析以下血压读数：

**本次读数**
- 收缩压：${params.systolic} mmHg
- 舒张压：${params.diastolic} mmHg
- 心率：${hrStr} bpm
- 测量时间：${params.measuredAt}（${tpLabel}）
- 用户备注：${params.notes || '无'}

**用户信息**
- 年龄：${ageStr}岁
- 性别：${genderStr}
- 高血压确诊年份：${diagStr}
- 目标血压：${params.targetSystolic}/${params.targetDiastolic} mmHg
- 当前用药：${medsStr}

**最近7次历史读数**（从旧到新）
${params.recentReadings || '（暂无历史记录）'}

请按照以下格式回复：

📊 **本次读数分析**
[血压等级分类 + 是否在目标范围内 + 与历史趋势对比]

💊 **用药提醒**
[根据用户用药清单给出提醒]

🍽️ **生活方式建议**
[2-3条针对本次读数的具体建议]

⚠️ **注意事项**
[风险评估、需要关注的问题]

${MEDICAL_DISCLAIMER}`;
}

// ── DeepSeek API Call ──

async function callDeepSeek(messages) {
  if (!DEEPSEEK_API_KEY) return 'AI分析服务未配置，请设置DEEPSEEK_API_KEY环境变量。您的血压数据已安全保存。';
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
    return result.choices?.[0]?.message?.content || 'AI分析返回为空，请稍后重试。';
  } catch (e) {
    console.error('DeepSeek API error:', e);
    return 'AI分析暂时不可用，请稍后再试。您的血压数据已安全保存。';
  }
}

// ── Main Handler ──

exports.main = async (event) => {
  const { OPENID } = cloud.getWXContext();
  if (!OPENID) return { errCode: 401, errMsg: '请先登录' };

  switch (event.action) {
    case 'create':  return createReading(OPENID, event.data || {});
    case 'list':    return listReadings(OPENID, event);
    case 'get':     return getReading(OPENID, event.id);
    case 'stats':   return getStats(OPENID, event.days || 7);
    case 'trends':  return getTrends(OPENID, event.days || 30);
    default:        return { errCode: 400, errMsg: '未知操作: ' + event.action };
  }
};

// ── Create Reading ──

async function createReading(openid, data) {
  const systolic = parseInt(data.systolic);
  const diastolic = parseInt(data.diastolic);
  const heartRate = data.heart_rate ? parseInt(data.heart_rate) : null;

  if (!systolic || !diastolic) return { errCode: 400, errMsg: '请填写收缩压和舒张压' };

  // Rate limit check
  const today = new Date().toISOString().split('T')[0];
  const { total } = await db.collection('readings')
    .where({ userId: openid, measuredDate: today }).count();
  if (total >= MAX_READINGS_PER_DAY) {
    return { errCode: 429, errMsg: '今日记录次数已达上限，请明天继续记录' };
  }

  // Get user profile
  const { data: users } = await db.collection('users').where({ openid }).get();
  const user = users.length > 0 ? users[0] : {};

  const bpLevel = classifyBp(systolic, diastolic);
  const emergency = isEmergency(systolic, diastolic, data.notes || '');

  let aiAnalysis = '';
  if (emergency) {
    aiAnalysis =
      '⚠️ **紧急提醒** ⚠️\n\n' +
      `您的血压读数为 ${systolic}/${diastolic} mmHg，已达到需立即就医的水平。\n\n` +
      '**请立即拨打120或前往最近的医院急诊科。**\n\n' +
      '您的血压数据已安全保存，可供医生参考。' +
      MEDICAL_DISCLAIMER;
  } else {
    // Get recent readings for context
    const { data: recent } = await db.collection('readings')
      .where({ userId: openid })
      .orderBy('measuredAt', 'desc')
      .limit(7)
      .get();

    let recentText = '（暂无历史记录）';
    if (recent.length > 0) {
      recentText = recent.reverse().map(r => {
        const hr = r.heartRate ? `心率${r.heartRate}` : '';
        const lvl = r.bpLevel ? ` [${r.bpLevel}]` : '';
        return `- ${r.measuredAt}（${r.timePeriod || '未指定'}）：${r.systolic}/${r.diastolic} ${hr}${lvl}`;
      }).join('\n');
    }

    const medsText = medicationSummary(user.medications || []);
    const prompt = buildReadingPrompt({
      systolic, diastolic, heartRate,
      measuredAt: data.measured_at || new Date().toISOString(),
      timePeriod: data.time_period || '',
      notes: data.notes || '',
      age: user.age || null,
      gender: user.gender || '',
      diagnosisYear: user.diagnosisYear || null,
      medications: medsText,
      targetSystolic: user.targetSystolic || 140,
      targetDiastolic: user.targetDiastolic || 90,
      recentReadings: recentText
    });

    aiAnalysis = await callDeepSeek([
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: prompt }
    ]);
  }

  const reading = {
    userId: openid,
    systolic,
    diastolic,
    heartRate,
    measuredAt: data.measured_at || new Date().toISOString(),
    measuredDate: (data.measured_at || new Date().toISOString()).split('T')[0],
    timePeriod: data.time_period || '',
    notes: (data.notes || '').slice(0, 200),
    aiAnalysis,
    bpLevel,
    createdAt: db.serverDate()
  };

  const result = await db.collection('readings').add({ data: reading });
  reading._id = result._id;

  // Log AI feedback
  await db.collection('ai_feedback').add({
    data: {
      userId: openid,
      readingId: result._id,
      promptType: 'reading_analysis',
      promptText: 'reading analysis prompt',
      responseText: aiAnalysis,
      createdAt: db.serverDate()
    }
  });

  return { errCode: 0, reading: formatReading(reading) };
}

// ── List Readings ──

async function listReadings(openid, event) {
  const page = event.page || 1;
  const limit = Math.min(event.limit || 20, 100);
  const skip = (page - 1) * limit;

  let condition = { userId: openid };
  if (event.start_date || event.end_date) {
    const dateCond = {};
    if (event.start_date) dateCond.$gte = event.start_date;
    if (event.end_date) dateCond.$lte = event.end_date;
    if (Object.keys(dateCond).length > 0) condition.measuredDate = dateCond;
  }

  const { total } = await db.collection('readings').where(condition).count();
  const { data: items } = await db.collection('readings')
    .where(condition)
    .orderBy('measuredAt', 'desc')
    .skip(skip)
    .limit(limit)
    .get();

  return {
    errCode: 0,
    items: items.map(formatReading),
    total,
    page,
    hasMore: skip + limit < total
  };
}

// ── Get Reading ──

async function getReading(openid, id) {
  if (!id) return { errCode: 400, errMsg: '缺少记录ID' };
  try {
    const { data } = await db.collection('readings').doc(id).get();
    if (!data || data.userId !== openid) return { errCode: 404, errMsg: '未找到该记录' };
    return { errCode: 0, reading: formatReading(data) };
  } catch {
    return { errCode: 404, errMsg: '未找到该记录' };
  }
}

// ── Get Stats ──

async function getStats(openid, days) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const cutoffStr = cutoff.toISOString().split('T')[0];

  const { data: rows } = await db.collection('readings')
    .where({ userId: openid, measuredDate: _.gte(cutoffStr) })
    .orderBy('measuredAt', 'asc')
    .get();

  if (rows.length === 0) {
    return { errCode: 0, stats: {
      avgSystolic: 0, avgDiastolic: 0, avgHeartRate: null,
      morningAvgSys: null, eveningAvgSys: null,
      readingCount: 0, daysWithReadings: 0,
      trendDirection: 'insufficient_data',
      highest: null, lowest: null
    }};
  }

  const count = rows.length;
  const daysSet = new Set(rows.map(r => r.measuredDate));
  const sysVals = rows.map(r => r.systolic);
  const diaVals = rows.map(r => r.diastolic);
  const hrVals = rows.filter(r => r.heartRate).map(r => r.heartRate);

  const morning = rows.filter(r => r.timePeriod === 'morning').map(r => r.systolic);
  const evening = rows.filter(r => ['evening', 'night'].includes(r.timePeriod)).map(r => r.systolic);

  const highest = rows.reduce((a, b) => a.systolic > b.systolic ? a : b);
  const lowest = rows.reduce((a, b) => a.systolic < b.systolic ? a : b);

  let direction = 'insufficient_data';
  if (count >= 4) {
    const half = Math.floor(count / 2);
    const firstAvg = sysVals.slice(0, half).reduce((s, v) => s + v, 0) / half;
    const secondAvg = sysVals.slice(half).reduce((s, v) => s + v, 0) / (count - half);
    const diff = secondAvg - firstAvg;
    if (diff < -5) direction = 'improving';
    else if (diff > 5) direction = 'worsening';
    else direction = 'stable';
  }

  return { errCode: 0, stats: {
    avgSystolic: round(sum(sysVals) / count),
    avgDiastolic: round(sum(diaVals) / count),
    avgHeartRate: hrVals.length > 0 ? round(sum(hrVals) / hrVals.length) : null,
    morningAvgSys: morning.length > 0 ? round(sum(morning) / morning.length) : null,
    eveningAvgSys: evening.length > 0 ? round(sum(evening) / evening.length) : null,
    readingCount: count,
    daysWithReadings: daysSet.size,
    trendDirection: direction,
    highest: { systolic: highest.systolic, diastolic: highest.diastolic, measuredAt: highest.measuredAt },
    lowest: { systolic: lowest.systolic, diastolic: lowest.diastolic, measuredAt: lowest.measuredAt }
  }};
}

// ── Get Trends ──

async function getTrends(openid, days) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const cutoffStr = cutoff.toISOString().split('T')[0];

  const { data: rows } = await db.collection('readings')
    .where({ userId: openid, measuredDate: _.gte(cutoffStr) })
    .orderBy('measuredAt', 'asc')
    .get();

  const dayData = {};
  for (const r of rows) {
    if (!dayData[r.measuredDate]) dayData[r.measuredDate] = [];
    dayData[r.measuredDate].push(r);
  }

  const dates = [];
  const systolic = [];
  const diastolic = [];
  const heartRate = [];

  for (const [d, dayRows] of Object.entries(dayData)) {
    dates.push(d);
    systolic.push(Math.round(sum(dayRows.map(r => r.systolic)) / dayRows.length));
    diastolic.push(Math.round(sum(dayRows.map(r => r.diastolic)) / dayRows.length));
    const hrVals = dayRows.filter(r => r.heartRate).map(r => r.heartRate);
    heartRate.push(hrVals.length > 0 ? Math.round(sum(hrVals) / hrVals.length) : null);
  }

  return { errCode: 0, dates, systolic, diastolic, heartRate };
}

// ── Helpers ──

function sum(arr) { return arr.reduce((a, b) => a + b, 0); }
function round(n) { return Math.round(n * 10) / 10; }

function formatReading(r) {
  return {
    id: r._id,
    user_id: r.userId,
    systolic: r.systolic,
    diastolic: r.diastolic,
    heart_rate: r.heartRate || null,
    measured_at: r.measuredAt,
    time_period: r.timePeriod || '',
    notes: r.notes || '',
    ai_analysis: r.aiAnalysis || '',
    bp_level: r.bpLevel || '',
    created_at: r.createdAt || r.measuredAt
  };
}
