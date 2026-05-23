const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();

exports.main = async (event) => {
  const { OPENID } = cloud.getWXContext();
  if (!OPENID) return { errCode: 401, errMsg: '微信登录失败，请重试' };

  const { data: users } = await db.collection('users').where({ openid: OPENID }).get();

  if (users.length > 0) {
    const user = users[0];
    await db.collection('users').doc(user._id).update({
      data: { updatedAt: db.serverDate() }
    });
    return { errCode: 0, user: formatUser(user) };
  }

  const result = await db.collection('users').add({
    data: {
      openid: OPENID,
      nickname: '',
      avatarUrl: '',
      age: null,
      gender: '',
      diagnosisYear: null,
      medications: [],
      targetSystolic: 140,
      targetDiastolic: 90,
      disclaimerAccepted: false,
      createdAt: db.serverDate(),
      updatedAt: db.serverDate()
    }
  });

  const { data: newUser } = await db.collection('users').doc(result._id).get();
  return { errCode: 0, user: formatUser(newUser) };
};

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
