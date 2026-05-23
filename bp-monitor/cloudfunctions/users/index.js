const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();

exports.main = async (event) => {
  const { OPENID } = cloud.getWXContext();
  if (!OPENID) return { errCode: 401, errMsg: '请先登录' };

  switch (event.action) {
    case 'getProfile':
      return getProfile(OPENID);
    case 'updateProfile':
      return updateProfile(OPENID, event.data || {});
    default:
      return { errCode: 400, errMsg: '未知操作: ' + event.action };
  }
};

async function getProfile(openid) {
  const { data: users } = await db.collection('users').where({ openid }).get();
  if (users.length === 0) return { errCode: 404, errMsg: '用户不存在' };
  return { errCode: 0, user: formatUser(users[0]) };
}

async function updateProfile(openid, updates) {
  const { data: users } = await db.collection('users').where({ openid }).get();
  if (users.length === 0) return { errCode: 404, errMsg: '用户不存在' };

  const user = users[0];
  const data = { updatedAt: db.serverDate() };

  if (updates.age !== undefined) data.age = updates.age;
  if (updates.gender !== undefined) data.gender = updates.gender;
  if (updates.diagnosis_year !== undefined) data.diagnosisYear = updates.diagnosis_year;
  if (updates.target_systolic !== undefined) data.targetSystolic = updates.target_systolic;
  if (updates.target_diastolic !== undefined) data.targetDiastolic = updates.target_diastolic;
  if (updates.medications !== undefined) {
    try {
      data.medications = typeof updates.medications === 'string'
        ? JSON.parse(updates.medications)
        : updates.medications;
    } catch {
      data.medications = [];
    }
  }

  await db.collection('users').doc(user._id).update({ data });
  const { data: updated } = await db.collection('users').doc(user._id).get();
  return { errCode: 0, user: formatUser(updated) };
}

function formatUser(user) {
  return {
    id: user._id,
    openid: user.openid,
    nickname: user.nickname || '',
    avatar_url: user.avatarUrl || '',
    age: user.age || null,
    gender: user.gender || '',
    diagnosis_year: user.diagnosisYear || null,
    medications: JSON.stringify(user.medications || []),
    target_systolic: user.targetSystolic || 140,
    target_diastolic: user.targetDiastolic || 90,
    disclaimer_accepted: user.disclaimerAccepted ? 1 : 0
  };
}
