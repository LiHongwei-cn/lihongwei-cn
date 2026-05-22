const cloud = require('wx-server-sdk');
const https = require('https');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const _ = db.command;

// ── Config ────────────────────────────────────────────────────
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const CRON_SECRET_TOKEN = process.env.CRON_SECRET_TOKEN || '';
const DEEPSEEK_BASE_URL = 'https://api.deepseek.com';
const DEEPSEEK_MODEL = 'deepseek-v4-pro';

// ── Rate limits ───────────────────────────────────────────────
const MAX_READINGS_PER_DAY = 10;

// ── BP Classification (from medical.py) ───────────────────────
function classifyBp(systolic, diastolic) {
  if (systolic >= 180 || diastolic >= 110) return '3级高血压（重度）';
  if (systolic >= 160 || diastolic >= 100) return '2级高血压（中度）';
  if (systolic >= 140 || diastolic >= 90) return '1级高血压（轻度）';
  if (systolic >= 130 || diastolic >= 85) return '正常高值';
  if (systolic >= 120 || diastolic >= 80) return '正常血压';
  return '理想血压';
}

function isEmergency(systolic, diastolic, notes) {
  if (systolic >= 180 || diastolic >= 110) {
    const kw = ['头痛', '视力模糊', '胸闷', '呼吸困难', '头晕', '胸痛', '说不清话', '无力', '恶心'];
    if (kw.some(k => (notes || '').includes(k))) return true;
  }
  if (systolic < 90) return true;
  return false;
}

function medicationSummary(medications) {
  let meds = medications;
  if (typeof meds === 'string') {
    try { meds = JSON.parse(meds); } catch (e) { return '未填写'; }
  }
  if (!Array.isArray(meds) || meds.length === 0) return '未填写';
  return meds.map(m => (m.name || '') + (m.dose ? ' ' + m.dose : '') + (m.time ? '（' + m.time + '）' : '')).join('、');
}

// ── Prompts (from prompts/) ───────────────────────────────────
const TIME_PERIOD_LABELS = {
  morning: '早晨（起床后1小时内）',
  afternoon: '下午',
  evening: '晚上（睡前1小时内）',
  night: '夜间',
};

const MEDICAL_DISCLAIMER = '\n---\n*以上分析由AI生成，仅供参考，不构成医疗诊断或处方。请以执业医师的诊断和治疗方案为准。如有不适，请及时就医。*';

const SYSTEM_PROMPT = `## 身份
你是一位专业的高血压健康管理助手。你的知识基于全球四大权威高血压指南：
1. WHO/ISH《全球高血压防治指南》
2. ACC/AHA《美国心脏病学会/美国心脏协会高血压指南》
3. ESC/ESH《欧洲心脏病学会/欧洲高血压学会动脉高血压管理指南》
4. 《中国高血压防治指南》

你为高血压患者及其家属提供血压解读、趋势分析和生活方式建议。

---
## 血压分级标准（诊室血压，单位 mmHg）
| 分类 | 收缩压 | 舒张压 |
|------|--------|--------|
| 理想血压 | <120 | 且 <80 |
| 正常血压 | 120-129 | 且/或 80-84 |
| 正常高值 | 130-139 | 且/或 85-89 |
| 1级高血压（轻度） | 140-159 | 且/或 90-99 |
| 2级高血压（中度） | 160-179 | 且/或 100-109 |
| 3级高血压（重度） | >=180 | 且/或 >=110 |

注：当收缩压和舒张压分属不同级别时，以较高的级别为准。

---
## 治疗目标
- 一般高血压患者：<140/90 mmHg
- 65-79岁老年人：<140/90 mmHg（如能耐受）
- 80岁以上高龄老人：<150/90 mmHg
- 合并糖尿病/肾病/冠心病：<130/80 mmHg
- 合并脑卒中：<140/90 mmHg

---
## 紧急就医指征
以下情况应立即就医或拨打120：
- 收缩压 >= 180 mmHg 且伴有头痛、视力模糊、胸闷、呼吸困难
- 任何血压水平伴有剧烈胸痛、言语不清、一侧肢体无力
- 收缩压 < 90 mmHg 且伴有头晕、冷汗

---
## 分析原则
1. 每次读数先按上述标准分级，明确告知用户血压等级
2. 结合用户的历史趋势进行分析（如提供历史数据）
3. 给出具体可执行的生活方式建议，不说泛泛之谈
4. 紧急情况立即建议就医，不得延误
5. 绝不自行为用户诊断疾病、推荐具体药物或调整药量
6. 所有建议前加"建议"二字
7. 默认使用中文回复

---
## 安全红线
1. 绝不建议用户自行停药、换药或调整药物剂量
2. 绝不替代执业医师的诊断和处方
3. 所有分析和建议仅供参考，以医生诊断为准
4. 遇到紧急指征必须立即建议就医
5. 不传播未经循证医学验证的偏方或保健品`;

function buildReadingPrompt(params) {
  const {
    systolic, diastolic, heartRate, measuredAt, timePeriod, notes,
    age, gender, diagnosisYear, medications,
    targetSystolic, targetDiastolic, recentReadings,
  } = params;
  const hr = heartRate || '未记录';
  const tp = TIME_PERIOD_LABELS[timePeriod] || timePeriod || '未指定';
  const ageStr = age ? String(age) : '未填写';
  const genderStr = gender || '未填写';
  const diagStr = diagnosisYear ? String(diagnosisYear) : '未填写';
  const medsStr = medications || '未填写';
  return `请分析以下血压读数：

**本次读数**
- 收缩压：${systolic} mmHg
- 舒张压：${diastolic} mmHg
- 心率：${hr} bpm
- 测量时间：${measuredAt}（${tp}）
- 用户备注：${notes || '无'}

**用户信息**
- 年龄：${ageStr}岁
- 性别：${genderStr}
- 高血压确诊年份：${diagStr}
- 目标血压：${targetSystolic}/${targetDiastolic} mmHg
- 当前用药：${medsStr}

**最近7次历史读数**（从旧到新）
${recentReadings}

请按照以下格式回复：

📊 **本次读数分析**
[血压等级分类 + 是否在目标范围内 + 与历史趋势对比]

💊 **用药提醒**
[根据用户用药清单给出提醒]

🍽️ **生活方式建议**
[2-3条针对本次读数的具体建议]

⚠️ **注意事项**
[风险评估、需要关注的问题、是否需要就医]

${MEDICAL_DISCLAIMER}`;
}

function buildWeeklyPrompt(params) {
  const {
    age, targetSystolic, targetDiastolic, weekStart, weekEnd, medications,
    readingCount, complianceRate, avgSystolic, avgDiastolic,
    morningAvg, eveningAvg, maxSystolic, maxDiastolic, maxTime,
    minSystolic, minDiastolic, minTime, stdSystolic, stdDiastolic,
    timeInRange, levelDistribution, dailySummary,
  } = params;
  const ageStr = age ? String(age) : '未填写';
  const medsStr = medications || '未填写';
  return `请根据以下一周血压数据生成综合健康周报：

**基本信息**
- 用户年龄：${ageStr}岁
- 目标血压：${targetSystolic}/${targetDiastolic} mmHg
- 报告周期：${weekStart} 至 ${weekEnd}
- 当前用药：${medsStr}

**本周统计**
- 总测量次数：${readingCount} 次（目标：14次，早晚各一次）
- 达标率：${complianceRate}%
- 平均血压：${avgSystolic}/${avgDiastolic} mmHg
- 早晨平均：${morningAvg} mmHg
- 晚上平均：${eveningAvg} mmHg
- 最高血压：${maxSystolic}/${maxDiastolic} mmHg（${maxTime}）
- 最低血压：${minSystolic}/${minDiastolic} mmHg（${minTime}）
- 血压波动（标准差）：收缩压±${stdSystolic}，舒张压±${stdDiastolic}
- 目标范围内时间占比：${timeInRange}%
- 血压分级分布：${levelDistribution}

**每日摘要**
${dailySummary}

请按以下格式回复：

📈 **本周血压趋势**
[整体趋势分析（改善/稳定/恶化），与目标对比，波动情况评估]

🔍 **关键发现**
[2-3个最重要的发现]

💊 **用药管理**
[用药依从性评估]

🏃 **生活方式评估**
[根据本周血压模式给出饮食、运动、盐摄入、情绪管理建议]

🎯 **下周目标**
[1-2个具体可量化的健康目标]

${MEDICAL_DISCLAIMER}`;
}

// ── DeepSeek API ──────────────────────────────────────────────
async function chat(messages) {
  if (!DEEPSEEK_API_KEY) return 'AI分析暂时不可用，请配置DEEPSEEK_API_KEY环境变量。您的血压数据已安全保存。';
  return new Promise(function (resolve) {
    var data = JSON.stringify({ model: DEEPSEEK_MODEL, messages: messages });
    var req = https.request({
      hostname: 'api.deepseek.com',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + DEEPSEEK_API_KEY },
      timeout: 60000
    }, function (res) {
      var body = '';
      res.on('data', function (chunk) { body += chunk; });
      res.on('end', function () {
        try { var json = JSON.parse(body); resolve(json.choices[0].message.content || ''); }
        catch (e) { console.error('DeepSeek parse error:', body); resolve('AI分析暂时不可用，请稍后再试。'); }
      });
    });
    req.on('error', function (e) { console.error('DeepSeek error:', e.message); resolve('AI分析暂时不可用，请稍后再试。'); });
    req.on('timeout', function () { req.destroy(); resolve('AI分析暂时不可用，请稍后再试。'); });
    req.write(data);
    req.end();
  });
}

// ── User helpers ──────────────────────────────────────────────
async function getUserByOpenid(openid) {
  const res = await db.collection('users').where({ _openid: openid }).get();
  return res.data.length > 0 ? res.data[0] : null;
}

// ── Action handlers ───────────────────────────────────────────

async function handleLogin(openid) {
  let user = await getUserByOpenid(openid);
  if (!user) {
    const newUser = {
      _openid: openid,
      nickname: '',
      avatarUrl: '',
      age: null,
      gender: '',
      diagnosisYear: null,
      medications: [],
      targetSystolic: 140,
      targetDiastolic: 90,
      disclaimerAccepted: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    const res = await db.collection('users').add({ data: newUser });
    user = { ...newUser, _id: res._id };
  }
  return { user: sanitizeUser(user) };
}

async function handleGetUserProfile(openid) {
  const user = await getUserByOpenid(openid);
  if (!user) return { error: '用户不存在' };
  return { user: sanitizeUser(user) };
}

async function handleUpdateUserProfile(openid, data) {
  const updates = {};
  const fields = ['age', 'gender', 'diagnosisYear', 'medications', 'targetSystolic', 'targetDiastolic', 'nickname', 'avatarUrl'];
  for (const f of fields) {
    if (data[f] !== undefined) updates[f] = data[f];
  }
  if (Object.keys(updates).length === 0) {
    const user = await getUserByOpenid(openid);
    return { user: sanitizeUser(user) };
  }
  updates.updatedAt = new Date();
  await db.collection('users').where({ _openid: openid }).update({ data: updates });
  const user = await getUserByOpenid(openid);
  return { user: sanitizeUser(user) };
}

// ── Reading handlers ──────────────────────────────────────────

async function handleAddReading(openid, data) {
  const { systolic, diastolic, heartRate, measuredAt, timePeriod, notes } = data;

  // Input validation
  if (typeof systolic !== 'number' || typeof diastolic !== 'number' ||
      systolic < 60 || systolic > 300 || diastolic < 30 || diastolic > 200) {
    return { error: '血压数值超出合理范围（收缩压60-300，舒张压30-200）' };
  }
  if (heartRate !== undefined && heartRate !== null && (typeof heartRate !== 'number' || heartRate < 30 || heartRate > 250)) {
    return { error: '心率数值超出合理范围（30-250 bpm）' };
  }

  // Rate limit check
  const todayStr = new Date().toISOString().substring(0, 10);
  const tomorrowStr = new Date(Date.now() + 86400000).toISOString().substring(0, 10);
  const dayCount = await db.collection('readings')
    .where({ _openid: openid, measuredAt: _.gte(todayStr).and(_.lt(tomorrowStr)) })
    .count();
  if (dayCount.total >= MAX_READINGS_PER_DAY) {
    return { error: '今日记录次数已达上限，请明天继续记录' };
  }

  const user = await getUserByOpenid(openid);
  if (!user) return { error: '用户不存在，请重新登录' };

  const reading = {
    _openid: openid,
    systolic,
    diastolic,
    heartRate: heartRate || null,
    measuredAt: measuredAt || new Date().toISOString(),
    timePeriod: timePeriod || '',
    notes: (notes || '').substring(0, 200),
    aiAnalysis: '',
    bpLevel: '',
    createdAt: new Date(),
  };

  const res = await db.collection('readings').add({ data: reading });
  const readingId = res._id;
  reading._id = readingId;

  // AI analysis
  const bpLevel = classifyBp(systolic, diastolic);
  const emergency = isEmergency(systolic, diastolic, reading.notes);

  let aiAnalysis;
  if (emergency) {
    aiAnalysis = '⚠️ **紧急提醒** ⚠️\n\n您的血压读数为 ' + systolic + '/' + diastolic
      + ' mmHg，已达到需立即就医的水平。\n\n**请立即拨打120或前往最近的医院急诊科。**\n\n'
      + '您的血压数据已安全保存，可供医生参考。' + MEDICAL_DISCLAIMER;
  } else {
    // Get recent readings
    const recentRes = await db.collection('readings')
      .where({ _openid: openid, _id: _.neq(readingId) })
      .orderBy('measuredAt', 'desc')
      .limit(7)
      .get();
    const recent = recentRes.data.reverse();
    let recentText = '（暂无历史记录）';
    if (recent.length > 0) {
      recentText = recent.map(r => {
        const hr = r.heartRate ? '心率' + r.heartRate : '';
        const lvl = r.bpLevel ? ' [' + r.bpLevel + ']' : '';
        return '- ' + r.measuredAt + '（' + (r.timePeriod || '未指定') + '）：' + r.systolic + '/' + r.diastolic + ' ' + hr + lvl;
      }).join('\n');
    }

    const medsText = medicationSummary(user.medications);
    const userMsg = buildReadingPrompt({
      systolic, diastolic, heartRate, measuredAt: reading.measuredAt,
      timePeriod: reading.timePeriod, notes: reading.notes,
      age: user.age, gender: user.gender, diagnosisYear: user.diagnosisYear,
      medications: medsText,
      targetSystolic: user.targetSystolic || 140,
      targetDiastolic: user.targetDiastolic || 90,
      recentReadings: recentText,
    });

    aiAnalysis = await chat([
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userMsg },
    ]);

    // Save AI feedback
    await db.collection('ai_feedback').add({ data: {
      _openid: openid,
      readingId,
      promptType: 'reading_analysis',
      promptText: userMsg,
      responseText: aiAnalysis,
      createdAt: new Date(),
    }});
  }

  await db.collection('readings').doc(readingId).update({
    data: { aiAnalysis, bpLevel },
  });
  reading.aiAnalysis = aiAnalysis;
  reading.bpLevel = bpLevel;

  return { reading };
}

async function handleGetReadings(openid, data) {
  const page = data.page || 1;
  const limit = Math.min(data.limit || 20, 100);
  const { startDate, endDate } = data;

  const conditions = { _openid: openid };
  if (startDate && endDate) {
    conditions.measuredAt = _.gte(startDate).and(_.lte(endDate + 'T23:59:59'));
  } else if (startDate) {
    conditions.measuredAt = _.gte(startDate);
  } else if (endDate) {
    conditions.measuredAt = _.lte(endDate + 'T23:59:59');
  }
  const query = db.collection('readings').where(conditions);

  const countRes = await query.count();
  const total = countRes.total;

  const res = await query
    .orderBy('measuredAt', 'desc')
    .skip((page - 1) * limit)
    .limit(limit)
    .get();

  return {
    items: res.data,
    total,
    page,
    hasMore: (page - 1) * limit + limit < total,
  };
}

async function handleGetStats(openid, data) {
  const days = data.days || 7;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  cutoff.setHours(0, 0, 0, 0);

  const res = await db.collection('readings')
    .where({ _openid: openid, measuredAt: _.gte(cutoff.toISOString()) })
    .orderBy('measuredAt', 'asc')
    .limit(500)
    .get();

  const rows = res.data;
  if (rows.length === 0) {
    return {
      avgSystolic: 0, avgDiastolic: 0, avgHeartRate: null,
      morningAvgSys: null, eveningAvgSys: null,
      readingCount: 0, daysWithReadings: 0,
      trendDirection: 'insufficient_data',
    };
  }

  const count = rows.length;
  const daysSet = new Set(rows.map(r => r.measuredAt.substring(0, 10)));
  const sysVals = rows.map(r => r.systolic);
  const diaVals = rows.map(r => r.diastolic);
  const hrVals = rows.filter(r => r.heartRate).map(r => r.heartRate);

  const morning = rows.filter(r => r.timePeriod === 'morning').map(r => r.systolic);
  const evening = rows.filter(r => ['evening', 'night'].includes(r.timePeriod)).map(r => r.systolic);

  let direction = 'insufficient_data';
  if (count >= 4) {
    const half = Math.floor(count / 2);
    const firstAvg = sysVals.slice(0, half).reduce((a, b) => a + b, 0) / half;
    const secondAvg = sysVals.slice(half).reduce((a, b) => a + b, 0) / (count - half);
    const diff = secondAvg - firstAvg;
    if (diff < -5) direction = 'improving';
    else if (diff > 5) direction = 'worsening';
    else direction = 'stable';
  }

  return {
    avgSystolic: round(sysVals.reduce((a, b) => a + b, 0) / count),
    avgDiastolic: round(diaVals.reduce((a, b) => a + b, 0) / count),
    avgHeartRate: hrVals.length ? round(hrVals.reduce((a, b) => a + b, 0) / hrVals.length) : null,
    morningAvgSys: morning.length ? round(morning.reduce((a, b) => a + b, 0) / morning.length) : null,
    eveningAvgSys: evening.length ? round(evening.reduce((a, b) => a + b, 0) / evening.length) : null,
    readingCount: count,
    daysWithReadings: daysSet.size,
    trendDirection: direction,
  };
}

// ── Report handlers ───────────────────────────────────────────

function getWeekBoundaries(referenceDate) {
  const dt = referenceDate ? new Date(referenceDate) : new Date();
  const day = dt.getDay();
  const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(dt);
  monday.setDate(diff);
  monday.setHours(0, 0, 0, 0);
  const sunday = new Date(monday);
  sunday.setDate(sunday.getDate() + 6);
  const fmt = d => d.toISOString().substring(0, 10);
  return { weekStart: fmt(monday), weekEnd: fmt(sunday) };
}

async function handleGenerateReport(openid, data) {
  const user = await getUserByOpenid(openid);
  if (!user) return { error: '用户不存在' };

  const { weekStart, weekEnd } = data.weekStart ? data : getWeekBoundaries();

  const readingsRes = await db.collection('readings')
    .where({ _openid: openid, measuredAt: _.gte(weekStart).and(_.lte(weekEnd + 'T23:59:59')) })
    .orderBy('measuredAt', 'asc')
    .limit(200)
    .get();
  const readings = readingsRes.data;

  if (readings.length === 0) {
    return { error: '本周（' + weekStart + ' 至 ' + weekEnd + '）暂无血压记录，无法生成报告' };
  }

  const count = readings.length;
  const sysVals = readings.map(r => r.systolic);
  const diaVals = readings.map(r => r.diastolic);
  const hrVals = readings.filter(r => r.heartRate).map(r => r.heartRate);

  const avgSys = sysVals.reduce((a, b) => a + b, 0) / count;
  const avgDia = diaVals.reduce((a, b) => a + b, 0) / count;

  const maxR = readings.reduce((a, b) => a.systolic > b.systolic ? a : b);
  const minR = readings.reduce((a, b) => a.systolic < b.systolic ? a : b);

  const morning = readings.filter(r => r.timePeriod === 'morning').map(r => r.systolic);
  const evening = readings.filter(r => ['evening', 'night'].includes(r.timePeriod)).map(r => r.systolic);

  const stdSys = count >= 2 ? stdDev(sysVals) : 0;
  const stdDia = count >= 2 ? stdDev(diaVals) : 0;

  const targetSys = user.targetSystolic || 140;
  const targetDia = user.targetDiastolic || 90;
  const inRange = readings.filter(r => r.systolic <= targetSys && r.diastolic <= targetDia).length;
  const timeInRange = (inRange / count) * 100;

  const levelCounts = {};
  readings.forEach(r => {
    const lvl = classifyBp(r.systolic, r.diastolic);
    levelCounts[lvl] = (levelCounts[lvl] || 0) + 1;
  });
  const levelParts = Object.entries(levelCounts).map(([lvl, n]) => lvl + ' ' + n + '次（' + Math.round(n / count * 100) + '%）');
  const levelDistribution = levelParts.join('、');

  const daysSet = new Set(readings.map(r => r.measuredAt.substring(0, 10)));
  const expected = daysSet.size * 2;
  const compliance = expected ? Math.min((count / expected) * 100, 100) : 0;

  // Daily summary
  const daily = {};
  readings.forEach(r => {
    const d = r.measuredAt.substring(0, 10);
    (daily[d] = daily[d] || []).push(r);
  });
  const dailyLines = Object.entries(daily).sort((a, b) => a[0].localeCompare(b[0])).map(([d, dayReads]) => {
    const parts = dayReads.map(r => '  ' + (r.timePeriod || '未知') + '：' + r.systolic + '/' + r.diastolic);
    return '- ' + d + '：\n' + parts.join('\n');
  });
  const dailySummary = dailyLines.join('\n');

  const medsText = medicationSummary(user.medications);
  const morningAvg = morning.length ? (morning.reduce((a, b) => a + b, 0) / morning.length).toFixed(1) : '无数据';
  const eveningAvg = evening.length ? (evening.reduce((a, b) => a + b, 0) / evening.length).toFixed(1) : '无数据';

  const userMsg = buildWeeklyPrompt({
    age: user.age,
    targetSystolic: targetSys, targetDiastolic: targetDia,
    weekStart, weekEnd, medications: medsText,
    readingCount: count, complianceRate: compliance.toFixed(1),
    avgSystolic: avgSys.toFixed(1), avgDiastolic: avgDia.toFixed(1),
    morningAvg, eveningAvg,
    maxSystolic: maxR.systolic, maxDiastolic: maxR.diastolic, maxTime: maxR.measuredAt,
    minSystolic: minR.systolic, minDiastolic: minR.diastolic, minTime: minR.measuredAt,
    stdSystolic: stdSys.toFixed(1), stdDiastolic: stdDia.toFixed(1),
    timeInRange: timeInRange.toFixed(1),
    levelDistribution, dailySummary,
  });

  const aiResponse = await chat([
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: userMsg },
  ]);

  const reportData = {
    _openid: openid,
    weekStart,
    weekEnd,
    avgSystolic: round(avgSys),
    avgDiastolic: round(avgDia),
    avgHeartRate: hrVals.length ? round(hrVals.reduce((a, b) => a + b, 0) / hrVals.length) : null,
    maxSystolic: maxR.systolic,
    maxDiastolic: maxR.diastolic,
    minSystolic: minR.systolic,
    minDiastolic: minR.diastolic,
    stdSystolic: round(stdSys),
    stdDiastolic: round(stdDia),
    readingCount: count,
    complianceRate: round(compliance),
    morningAvgSys: morning.length ? round(morning.reduce((a, b) => a + b, 0) / morning.length) : null,
    eveningAvgSys: evening.length ? round(evening.reduce((a, b) => a + b, 0) / evening.length) : null,
    timeInRange: round(timeInRange),
    trendSummary: aiResponse,
    recommendations: '',
    createdAt: new Date(),
  };

  // Upsert
  const existing = await db.collection('reports').where({ _openid: openid, weekStart }).get();
  let report;
  if (existing.data.length > 0) {
    await db.collection('reports').doc(existing.data[0]._id).update({ data: reportData });
    report = { ...reportData, _id: existing.data[0]._id };
  } else {
    const res = await db.collection('reports').add({ data: reportData });
    report = { ...reportData, _id: res._id };
  }

  // Save AI feedback
  await db.collection('ai_feedback').add({ data: {
    _openid: openid,
    promptType: 'weekly_report',
    promptText: userMsg,
    responseText: aiResponse,
    createdAt: new Date(),
  }});

  return { report };
}

async function handleGetReports(openid) {
  const res = await db.collection('reports')
    .where({ _openid: openid })
    .orderBy('weekStart', 'desc')
    .limit(52)
    .get();
  return { reports: res.data };
}

// ── Math helpers ──────────────────────────────────────────────

function round(n) { return Math.round(n * 10) / 10; }

function stdDev(arr) {
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  const variance = arr.reduce((s, v) => s + (v - mean) * (v - mean), 0) / arr.length;
  return Math.sqrt(variance);
}

function sanitizeUser(u) {
  return {
    _id: u._id,
    nickname: u.nickname || '',
    avatarUrl: u.avatarUrl || '',
    age: u.age || null,
    gender: u.gender || '',
    diagnosisYear: u.diagnosisYear || null,
    medications: u.medications || [],
    targetSystolic: u.targetSystolic || 140,
    targetDiastolic: u.targetDiastolic || 90,
    disclaimerAccepted: u.disclaimerAccepted || 0,
    createdAt: u.createdAt,
  };
}

// ── Main ──────────────────────────────────────────────────────

exports.main = async (event, context) => {
  const { action, data } = event;
  const { OPENID } = cloud.getWXContext();

  if (!OPENID) {
    return { error: '未能获取用户身份，请在微信环境中使用' };
  }

  try {
    switch (action) {
      case 'login':
        return await handleLogin(OPENID);
      case 'getUserProfile':
        return await handleGetUserProfile(OPENID);
      case 'updateUserProfile':
        return await handleUpdateUserProfile(OPENID, data || {});
      case 'addReading':
        return await handleAddReading(OPENID, data || {});
      case 'getReadings':
        return await handleGetReadings(OPENID, data || {});
      case 'getStats':
        return await handleGetStats(OPENID, data || {});
      case 'generateReport':
        return await handleGenerateReport(OPENID, data || {});
      case 'getReports':
        return await handleGetReports(OPENID);
      default:
        return { error: '未知操作: ' + action };
    }
  } catch (e) {
    console.error('Cloud function error:', e);
    return { error: e.message || '服务器内部错误' };
  }
};
