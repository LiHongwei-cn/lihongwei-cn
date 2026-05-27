%% 批量测试所有 MATLAB 脚本
% 功能：依次运行所有示例脚本和工具函数，报告通过/失败结果
% 兼容版本：MATLAB R2016b

scriptDir = fileparts(mfilename('fullpath'));
addpath(scriptDir);
addpath(fullfile(scriptDir, 'utils'));
addpath(fullfile(scriptDir, 'examples'));

passed = 0;
failed = 0;

fprintf('\n========== Testing Utility Functions ==========\n');

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

fprintf('\n========== Testing Example Scripts ==========\n');

tests = {
    'vehicle_dynamics',        @vehicle_dynamics;
    'motor_control',           @motor_control;
    'dc_motor_pwm',            @dc_motor_pwm;
    'ev_dynamics_simple',      @ev_dynamics_simple;
    'battery_soc_ekf',         @battery_soc_ekf;
    'driving_cycle_analysis',  @driving_cycle_analysis;
    'energy_management',       @energy_management;
};

for i = 1:size(tests, 1)
    name = tests{i, 1};
    func = tests{i, 2};
    try
        func();
        fprintf('[PASS] %s\n', name); passed = passed + 1;
    catch e
        fprintf('[FAIL] %s: %s\n', name, e.message); failed = failed + 1;
    end
    close all;
end

fprintf('\n========== Testing ADAS HIL Demo ==========\n');

try
    addpath(fullfile(scriptDir, 'examples', 'adas_hil_demo'));
    main_adas_hil_demo;
    fprintf('[PASS] main_adas_hil_demo\n'); passed = passed + 1;
catch e
    fprintf('[FAIL] main_adas_hil_demo: %s\n', e.message); failed = failed + 1;
end
close all;

fprintf('\n========== Results: %d PASS / %d FAIL ==========\n', passed, failed);
