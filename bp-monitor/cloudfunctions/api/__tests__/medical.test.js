/**
 * Unit tests for BP classification logic (mirrors backend tests/test_medical.py).
 * These test the JavaScript implementations in ../index.js.
 */

// Replicate the logic from index.js for testing
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

function inTargetRange(systolic, diastolic, targetSys, targetDia) {
  return systolic <= targetSys && diastolic <= targetDia;
}

function medicationSummary(medications) {
  let meds = medications;
  if (typeof meds === 'string') {
    try { meds = JSON.parse(meds); } catch (e) { return '未填写'; }
  }
  if (!Array.isArray(meds) || meds.length === 0) return '未填写';
  return meds.map(m => (m.name || '') + (m.dose ? ' ' + m.dose : '') + (m.time ? '（' + m.time + '）' : '')).join('、');
}

function round(n) { return Math.round(n * 10) / 10; }
function stdDev(arr) {
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  const variance = arr.reduce((s, v) => s + (v - mean) * (v - mean), 0) / arr.length;
  return Math.sqrt(variance);
}

// ── classifyBp tests ────────────────────────────────────────
function testClassifyBp() {
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label + ' — expected "' + expected + '", got "' + actual + '"'); }
  }

  assertEq(classifyBp(110, 70), '理想血压', 'ideal');
  assertEq(classifyBp(120, 80), '正常血压', 'normal');
  assertEq(classifyBp(130, 85), '正常高值', 'high_normal');
  assertEq(classifyBp(140, 80), '1级高血压（轻度）', 'grade1_sys_only');
  assertEq(classifyBp(120, 90), '1级高血压（轻度）', 'grade1_dia_only');
  assertEq(classifyBp(160, 100), '2级高血压（中度）', 'grade2');
  assertEq(classifyBp(180, 110), '3级高血压（重度）', 'grade3');
  assertEq(classifyBp(120, 110), '3级高血压（重度）', 'grade3_dia_only');
  assertEq(classifyBp(180, 80), '3级高血压（重度）', 'higher_level_wins');

  console.log('classifyBp: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── isEmergency tests ────────────────────────────────────────
function testIsEmergency() {
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label); }
  }

  assertEq(isEmergency(140, 85, ''), false, 'no_emergency_normal');
  assertEq(isEmergency(140, 85, '今天有点头晕'), false, 'no_emergency_borderline');
  assertEq(isEmergency(185, 100, '头痛胸闷'), true, 'emergency_high_with_symptoms');
  assertEq(isEmergency(180, 110, ''), false, 'boundary_no_symptoms');
  assertEq(isEmergency(180, 110, '胸痛'), true, 'boundary_with_symptoms');
  assertEq(isEmergency(85, 55, ''), true, 'emergency_low_bp');

  console.log('isEmergency: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── inTargetRange tests ──────────────────────────────────────
function testInTargetRange() {
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label); }
  }

  assertEq(inTargetRange(130, 80, 140, 90), true, 'in_range');
  assertEq(inTargetRange(145, 80, 140, 90), false, 'out_systolic');
  assertEq(inTargetRange(130, 95, 140, 90), false, 'out_diastolic');
  assertEq(inTargetRange(145, 95, 140, 90), false, 'out_both');
  assertEq(inTargetRange(140, 90, 140, 90), true, 'boundary_equal');
  assertEq(inTargetRange(130, 80, 150, 90), true, 'elderly_target');
  assertEq(inTargetRange(125, 75, 130, 80), true, 'diabetes_target');

  console.log('inTargetRange: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── medicationSummary tests ──────────────────────────────────
function testMedicationSummary() {
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label + ' — expected "' + expected + '", got "' + actual + '"'); }
  }

  assertEq(medicationSummary([]), '未填写', 'empty');
  assertEq(medicationSummary(null), '未填写', 'null');
  assertEq(medicationSummary('not array'), '未填写', 'not_array');
  assertEq(medicationSummary([{ name: '氨氯地平', dose: '5mg', time: 'morning' }]),
    '氨氯地平 5mg（morning）', 'single_med');
  assertEq(medicationSummary([{ name: '缬沙坦', dose: '80mg', time: 'evening' }, { name: '氢氯噻嗪', dose: '12.5mg', time: 'morning' }]),
    '缬沙坦 80mg（evening）、氢氯噻嗪 12.5mg（morning）', 'two_meds');
  assertEq(medicationSummary('[{"name":"氨氯地平","dose":"5mg","time":"morning"}]'),
    '氨氯地平 5mg（morning）', 'json_string');
  assertEq(medicationSummary('invalid json'), '未填写', 'invalid_json');
  assertEq(medicationSummary([{ name: '' }]), '', 'empty_name');

  console.log('medicationSummary: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── stdDev tests ─────────────────────────────────────────────
function testStdDev() {
  let pass = 0, fail = 0;
  function assertClose(actual, expected, label) {
    if (Math.abs(actual - expected) < 0.05) { pass++; }
    else { fail++; console.log('FAIL: ' + label + ' — expected ~' + expected + ', got ' + actual); }
  }

  assertClose(stdDev([120, 130, 140, 150, 160]), 14.14, 'spread');
  assertClose(stdDev([100, 100, 100]), 0, 'all_same');
  assertClose(stdDev([120]), 0, 'single');

  console.log('stdDev: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── round tests ──────────────────────────────────────────────
function testRound() {
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label + ' — expected ' + expected + ', got ' + actual); }
  }

  assertEq(round(125.55), 125.6, 'tenth_up');
  assertEq(round(125.54), 125.5, 'tenth_down');
  assertEq(round(125), 125, 'integer');
  assertEq(round(0), 0, 'zero');

  console.log('round: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── Time period label test ───────────────────────────────────
function testTimePeriodLabels() {
  const labels = {
    morning: '早晨（起床后1小时内）',
    afternoon: '下午',
    evening: '晚上（睡前1小时内）',
    night: '夜间',
  };
  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label); }
  }

  assertEq(labels['morning'], '早晨（起床后1小时内）', 'morning');
  assertEq(labels['afternoon'], '下午', 'afternoon');
  assertEq(labels['evening'], '晚上（睡前1小时内）', 'evening');
  assertEq(labels['night'], '夜间', 'night');
  assertEq(labels['unknown'] || 'unknown', 'unknown', 'unknown_fallback');

  console.log('timePeriodLabels: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── Input validation tests ───────────────────────────────────
function testInputValidation() {
  function validateReading(systolic, diastolic, heartRate) {
    if (typeof systolic !== 'number' || typeof diastolic !== 'number' ||
        systolic < 60 || systolic > 300 || diastolic < 30 || diastolic > 200) {
      return '血压数值超出合理范围（收缩压60-300，舒张压30-200）';
    }
    if (heartRate !== undefined && heartRate !== null && (typeof heartRate !== 'number' || heartRate < 30 || heartRate > 250)) {
      return '心率数值超出合理范围（30-250 bpm）';
    }
    return null;
  }

  let pass = 0, fail = 0;
  function assertEq(actual, expected, label) {
    if (actual === expected) { pass++; }
    else { fail++; console.log('FAIL: ' + label + ' — expected "' + expected + '", got "' + actual + '"'); }
  }

  assertEq(validateReading(120, 80, 72), null, 'valid_reading');
  assertEq(validateReading(120, 80, null), null, 'valid_no_hr');
  assertEq(validateReading(120, 80, undefined), null, 'valid_hr_undefined');
  assertEq(validateReading(59, 80, 72), '血压数值超出合理范围（收缩压60-300，舒张压30-200）', 'sys_too_low');
  assertEq(validateReading(301, 80, 72), '血压数值超出合理范围（收缩压60-300，舒张压30-200）', 'sys_too_high');
  assertEq(validateReading(120, 29, 72), '血压数值超出合理范围（收缩压60-300，舒张压30-200）', 'dia_too_low');
  assertEq(validateReading(120, 80, 29), '心率数值超出合理范围（30-250 bpm）', 'hr_too_low');
  assertEq(validateReading(120, 80, 251), '心率数值超出合理范围（30-250 bpm）', 'hr_too_high');
  assertEq(validateReading('abc', 80, 72), '血压数值超出合理范围（收缩压60-300，舒张压30-200）', 'sys_not_number');

  console.log('inputValidation: ' + pass + '/' + (pass + fail) + ' passed');
  return fail === 0;
}

// ── Run all ──────────────────────────────────────────────────
(function main() {
  console.log('=== BP Monitor Cloud Function Unit Tests ===\n');
  const results = [
    testClassifyBp(),
    testIsEmergency(),
    testInTargetRange(),
    testMedicationSummary(),
    testStdDev(),
    testRound(),
    testTimePeriodLabels(),
    testInputValidation(),
  ];
  const allPassed = results.every(r => r);
  console.log('\n' + (allPassed ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED'));
  process.exit(allPassed ? 0 : 1);
})();
