%% 批量测试所有 MATLAB 脚本
% R2016b 兼容

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
    fprintf('[通过] rms_calculation\n'); passed = passed + 1;
catch e
    fprintf('[失败] rms_calculation: %s\n', e.message); failed = failed + 1;
end

try
    [f, m] = fft_analysis(sin(2*pi*50*(0:0.001:0.1)), 1000);
    assert(length(f) == 51);
    fprintf('[通过] fft_analysis\n'); passed = passed + 1;
catch e
    fprintf('[失败] fft_analysis: %s\n', e.message); failed = failed + 1;
end

try
    t = 0:0.001:1;
    x = sin(2*pi*10*t) + 0.5*randn(size(t));
    y = lowpass_filter(x, 30, 1000);
    assert(length(y) == length(x));
    fprintf('[通过] lowpass_filter\n'); passed = passed + 1;
catch e
    fprintf('[失败] lowpass_filter: %s\n', e.message); failed = failed + 1;
end

fprintf('\n========== 测试 examples ==========\n');

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
        fprintf('[通过] %s\n', name);
        passed = passed + 1;
    catch e
        fprintf('[失败] %s: %s\n', name, e.message);
        failed = failed + 1;
    end
    close all;
end

fprintf('\n========== 测试 ADAS HIL Demo ==========\n');

try
    addpath(fullfile(scriptDir, 'examples', 'adas_hil_demo'));
    main_adas_hil_demo;
    fprintf('[通过] main_adas_hil_demo\n'); passed = passed + 1;
catch e
    fprintf('[失败] main_adas_hil_demo: %s\n', e.message); failed = failed + 1;
end
close all;

fprintf('\n========== 结果: %d 通过 / %d 失败 ==========\n', passed, failed);
