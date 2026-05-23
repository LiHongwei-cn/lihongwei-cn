const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const _ = db.command;

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';

function classifyBp(systolic, diastolic) {
  if (systolic >= 180 || diastolic >= 110) return '3级高血压（重度）';
  if (systolic >= 160 || diastolic >= 100) return '2级高血压（中度）';
  if (systolic >= 140 || diastolic >= 90)  return '1级高血压（轻度）';
  if (systolic >= 130 || diastolic >= 85)  return '正常高值';
  if (systolic >= 120 || diastolic >= 80)  return '正常血压';
  return '理想血压';
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

const SYSTEM_PROMPT = `## 身份
你是一位专业的高血压健康管理助手。你的知识基于全球四大权威高血压指南。
你为高血压患者提供血压解读、趋势分析和生活方式建议。
默认使用中文回复。

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
3. 遇到紧急指征必须立即建议就医`;

const MEDICAL_DISCLAIMER = '\n---\n*以上分析由AI生成，仅供参考，不构成医疗诊断或处方。*';

async function callDeepSeek(messages) {
  if (!DEEPSEEK_API_KEY) return 'AI分析服务未配置。';
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
    return result.choices?.[0]?.message?.content || '';
  } catch (e) {
    console.error('DeepSeek error:', e);
    return 'AI分析暂时不可用。';
  }
}

function getWeekBoundaries(refDate) {
  const dt = refDate ? new Date(refDate) : new Date();
  const day = dt.getDay();
  const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(dt.setDate(diff));
  const sunday = new Date(monday);
  sunday.setDate(sunday.getDate() + 6);
  return {
    weekStart: monday.toISOString().split('T')[0],
    weekEnd: sunday.toISOString().split('T')[0]
  };
}

function stdev(values) {
  if (values.length < 2) return 0;
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  return Math.sqrt(values.reduce((s, v) => s + (v - avg) ** 2, 0) / (values.length - 1));
}

// ── Main Handler ──

exports.main = async (event) => {
  const { OPENID } = cloud.getWXContext();

  switch (event.action) {
    case 'list':    return listReports(OPENID);
    case 'latest':  return latestReport(OPENID);
    case 'get':     return getReport(OPENID, event.id);
    case 'generate': return generateReport(OPENID, event.allUsers);
    default:        return { errCode: 400, errMsg: '未知操作: ' + event.action };
  }
};

// ── List ──

async function listReports(openid) {
  if (!openid) return { errCode: 401, errMsg: '请先登录' };
  const { data: items } = await db.collection('reports')
    .where({ userId: openid })
    .orderBy('weekStart', 'desc')
    .limit(52)
    .get();
  return { errCode: 0, reports: items.map(formatReport) };
}

// ── Latest ──

async function latestReport(openid) {
  if (!openid) return { errCode: 401, errMsg: '请先登录' };
  const { data: items } = await db.collection('reports')
    .where({ userId: openid })
    .orderBy('weekStart', 'desc')
    .limit(1)
    .get();
  if (items.length === 0) return { errCode: 404, errMsg: '暂无报告，请先生成' };
  return { errCode: 0, report: formatReport(items[0]) };
}

// ── Get ──

async function getReport(openid, id) {
  if (!openid) return { errCode: 401, errMsg: '请先登录' };
  try {
    const { data } = await db.collection('reports').doc(id).get();
    if (!data || data.userId !== openid) return { errCode: 404, errMsg: '未找到该报告' };
    return { errCode: 0, report: formatReport(data) };
  } catch {
    return { errCode: 404, errMsg: '未找到该报告' };
  }
}

// ── Generate ──

async function generateReport(openid, allUsers) {
  if (allUsers) {
    const { data: users } = await db.collection('users').get();
    const results = [];
    for (const user of users) {
      try {
        const report = await generateForUser(user);
        results.push(report);
      } catch (e) {
        if (e.message !== 'NO_READINGS') console.error('Report error:', e);
      }
    }
    if (results.length === 0) return { errCode: 400, errMsg: '本周暂无用户有血压记录' };
    return { errCode: 0, report: results[0] };
  }

  if (!openid) return { errCode: 401, errMsg: '请先登录' };
  const { data: users } = await db.collection('users').where({ openid }).get();
  if (users.length === 0) return { errCode: 404, errMsg: '用户不存在' };

  try {
    const report = await generateForUser(users[0]);
    return { errCode: 0, report };
  } catch (e) {
    return { errCode: 400, errMsg: e.message };
  }
}

async function generateForUser(user) {
  const openid = user.openid;
  const { weekStart, weekEnd } = getWeekBoundaries();

  const { data: readings } = await db.collection('readings')
    .where({ userId: openid, measuredDate: _.gte(weekStart).and(_.lte(weekEnd)) })
    .orderBy('measuredAt', 'asc')
    .get();

  if (readings.length === 0) throw new Error('NO_READINGS');

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

  const stdSys = stdev(sysVals);
  const stdDia = stdev(diaVals);

  const targetSys = user.targetSystolic || 140;
  const targetDia = user.targetDiastolic || 90;
  const inRange = readings.filter(r => r.systolic <= targetSys && r.diastolic <= targetDia).length;
  const timeInRange = (inRange / count) * 100;

  // Level distribution
  const levelCounts = {};
  for (const r of readings) {
    const lvl = classifyBp(r.systolic, r.diastolic);
    levelCounts[lvl] = (levelCounts[lvl] || 0) + 1;
  }
  const levelDist = Object.entries(levelCounts)
    .map(([lvl, n]) => `${lvl} ${n}次（${Math.round(n / count * 100)}%）`).join('、');

  // Compliance
  const daysSet = new Set(readings.map(r => r.measuredDate));
  const expected = daysSet.size * 2;
  const compliance = expected ? Math.min((count / expected) * 100, 100) : 0;

  // Daily summary
  const daily = {};
  for (const r of readings) {
    if (!daily[r.measuredDate]) daily[r.measuredDate] = [];
    daily[r.measuredDate].push(r);
  }
  const dailyLines = [];
  for (const [d, dayRows] of Object.entries(daily).sort()) {
    const parts = dayRows.map(r => `  ${r.timePeriod || '未知'}：${r.systolic}/${r.diastolic}`);
    dailyLines.push(`- ${d}：\n${parts.join('\n')}`);
  }

  const medsText = medicationSummary(user.medications || []);

  // Build prompt
  const prompt = `请根据以下一周血压数据生成综合健康周报：

**基本信息**
- 用户年龄：${user.age || '未填写'}岁
- 目标血压：${targetSys}/${targetDia} mmHg
- 报告周期：${weekStart} 至 ${weekEnd}
- 当前用药：${medsText}

**本周统计**
- 总测量次数：${count} 次（目标：14次，早晚各一次）
- 达标率：${compliance.toFixed(1)}%
- 平均血压：${avgSys.toFixed(1)}/${avgDia.toFixed(1)} mmHg
- 早晨平均：${morning.length > 0 ? (morning.reduce((a,b) => a + b, 0) / morning.length).toFixed(1) : '无数据'} mmHg
- 晚上平均：${evening.length > 0 ? (evening.reduce((a,b) => a + b, 0) / evening.length).toFixed(1) : '无数据'} mmHg
- 最高血压：${maxR.systolic}/${maxR.diastolic} mmHg（${maxR.measuredAt}）
- 最低血压：${minR.systolic}/${minR.diastolic} mmHg（${minR.measuredAt}）
- 血压波动（标准差）：收缩压±${stdSys.toFixed(1)}，舒张压±${stdDia.toFixed(1)}
- 目标范围内时间占比：${timeInRange.toFixed(1)}%
- 血压分级分布：${levelDist}

**每日摘要**
${dailyLines.join('\n')}

请按以下格式回复：
📈 **本周血压趋势**
🔍 **关键发现**
💊 **用药管理**
🏃 **生活方式评估**
🎯 **下周目标**
${MEDICAL_DISCLAIMER}`;

  const aiResponse = await callDeepSeek([
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: prompt }
  ]);

  // Upsert report
  const { data: existing } = await db.collection('reports')
    .where({ userId: openid, weekStart }).get();

  const reportData = {
    userId: openid,
    weekStart,
    weekEnd,
    avgSystolic: Math.round(avgSys * 10) / 10,
    avgDiastolic: Math.round(avgDia * 10) / 10,
    avgHeartRate: hrVals.length > 0 ? Math.round(hrVals.reduce((a,b) => a + b, 0) / hrVals.length * 10) / 10 : null,
    maxSystolic: maxR.systolic,
    maxDiastolic: maxR.diastolic,
    minSystolic: minR.systolic,
    minDiastolic: minR.diastolic,
    stdSystolic: Math.round(stdSys * 10) / 10,
    stdDiastolic: Math.round(stdDia * 10) / 10,
    readingCount: count,
    complianceRate: Math.round(compliance * 10) / 10,
    morningAvgSys: morning.length > 0 ? Math.round(morning.reduce((a,b) => a + b, 0) / morning.length * 10) / 10 : null,
    eveningAvgSys: evening.length > 0 ? Math.round(evening.reduce((a,b) => a + b, 0) / evening.length * 10) / 10 : null,
    timeInRange: Math.round(timeInRange * 10) / 10,
    trendSummary: aiResponse,
    recommendations: '',
    updatedAt: db.serverDate()
  };

  if (existing.length > 0) {
    await db.collection('reports').doc(existing[0]._id).update({ data: reportData });
  } else {
    reportData.createdAt = db.serverDate();
    await db.collection('reports').add({ data: reportData });
  }

  // Log AI feedback
  await db.collection('ai_feedback').add({
    data: {
      userId: openid,
      promptType: 'weekly_report',
      promptText: 'weekly report prompt',
      responseText: aiResponse,
      createdAt: db.serverDate()
    }
  });

  const { data: saved } = await db.collection('reports')
    .where({ userId: openid, weekStart }).get();
  return formatReport(saved[0]);
}

// ── Helpers ──

function formatReport(r) {
  return {
    id: r._id,
    user_id: r.userId,
    week_start: r.weekStart,
    week_end: r.weekEnd,
    avg_systolic: r.avgSystolic,
    avg_diastolic: r.avgDiastolic,
    avg_heart_rate: r.avgHeartRate || null,
    max_systolic: r.maxSystolic,
    max_diastolic: r.maxDiastolic,
    min_systolic: r.minSystolic,
    min_diastolic: r.minDiastolic,
    std_systolic: r.stdSystolic,
    std_diastolic: r.stdDiastolic,
    reading_count: r.readingCount || 0,
    compliance_rate: r.complianceRate || 0,
    morning_avg_sys: r.morningAvgSys,
    evening_avg_sys: r.eveningAvgSys,
    time_in_range: r.timeInRange || 0,
    trend_summary: r.trendSummary || '',
    recommendations: r.recommendations || '',
    created_at: r.createdAt || r.weekStart
  };
}
