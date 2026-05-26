%% Batch test all MATLAB scripts
% R2016b compatible

scriptDir = fileparts(mfilename('fullpath'));
addpath(scriptDir);
addpath(fullfile(scriptDir, 'utils'));
addpath(fullfile(scriptDir, 'examples'));

passed = 0;
failed = 0;

fprintf('\n========== 测试 utils ==========\n');

try
    r = rms_calculation([1 2 3 4 5]);
    assert(abs(r - 3.3166) < 0.001);
    fprintf('[PASS] rms_calculation\n'); passed = passed + 1;
catch e
    fprintf('[FAIL] rms_calculation: %s\n', e.message); failed = failed + 1;
end

try
    [f, m] = fft_analysis(sin(2*pi*50*(0:0.001:0.1)), 1000);
    assert(length(f) == 51);
    fprintf('[PASS] fft_analysis\n'); passed = passed + 1;
catch e
    fprintf('[FAIL] fft_analysis: %s\n', e.message); failed = failed + 1;
end

try
    t = 0:0.001:1;
    x = sin(2*pi*10*t) + 0.5*randn(size(t));
    y = lowpass_filter(x, 30, 1000);
    assert(length(y) == length(x));
    fprintf('[PASS] lowpass_filter\n'); passed = passed + 1;
catch e
    fprintf('[FAIL] lowpass_filter: %s\n', e.message); failed = failed + 1;
end

fprintf('\n========== 测试 ADAS HIL Demo ==========\n');

try
    addpath(fullfile(scriptDir, 'examples', 'adas_hil_demo'));
    main_adas_hil_demo;
    fprintf('[PASS] main_adas_hil_demo\n'); passed = passed + 1;
catch e
    fprintf('[FAIL] main_adas_hil_demo: %s\n', e.message); failed = failed + 1;
end

fprintf('\n========== 结果: %d 通过 / %d 失败 ==========\n', passed, failed);
