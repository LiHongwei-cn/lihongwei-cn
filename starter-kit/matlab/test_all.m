%% Batch test all MATLAB scripts
% R2016b compatible
% Each example runs in isolated sub-function

scriptDir = fileparts(mfilename('fullpath'));
addpath(scriptDir);
addpath(fullfile(scriptDir, 'utils'));
addpath(fullfile(scriptDir, 'examples'));
addpath(fullfile(scriptDir, 'carsim'));

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

fprintf('\n========== 测试 examples ==========\n');

[ok, msg] = test_vd();  %#ok
if ok, fprintf('[PASS] vehicle_dynamics\n'); passed = passed + 1;
else fprintf('[FAIL] vehicle_dynamics: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_mc();
if ok, fprintf('[PASS] motor_control\n'); passed = passed + 1;
else fprintf('[FAIL] motor_control: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_dc();
if ok, fprintf('[PASS] dc_motor_pwm\n'); passed = passed + 1;
else fprintf('[FAIL] dc_motor_pwm: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_ev();
if ok, fprintf('[PASS] ev_dynamics_simple\n'); passed = passed + 1;
else fprintf('[FAIL] ev_dynamics_simple: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_soc();
if ok, fprintf('[PASS] battery_soc_ekf\n'); passed = passed + 1;
else fprintf('[FAIL] battery_soc_ekf: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_drv_cyc();
if ok, fprintf('[PASS] driving_cycle_analysis\n'); passed = passed + 1;
else fprintf('[FAIL] driving_cycle_analysis: %s\n', msg); failed = failed + 1; end

[ok, msg] = test_ems();
if ok, fprintf('[PASS] energy_management\n'); passed = passed + 1;
else fprintf('[FAIL] energy_management: %s\n', msg); failed = failed + 1; end

fprintf('\n========== 结果: %d 通过 / %d 失败 ==========\n', passed, failed);
exit;

function [ok, msg] = test_vd()
    ok = false; msg = '';
    try
        vehicle_dynamics; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_mc()
    ok = false; msg = '';
    try
        motor_control; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_dc()
    ok = false; msg = '';
    try
        dc_motor_pwm; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_ev()
    ok = false; msg = '';
    try
        ev_dynamics_simple; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_soc()
    ok = false; msg = '';
    try
        battery_soc_ekf; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_drv_cyc()
    ok = false; msg = '';
    try
        driving_cycle_analysis; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end

function [ok, msg] = test_ems()
    ok = false; msg = '';
    try
        energy_management; %#ok
        ok = true; msg = '';
    catch e
        ok = false; msg = e.message;
    end
    close all;
end
