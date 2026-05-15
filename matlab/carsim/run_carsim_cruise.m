%% One-click CarSim-Simulink co-simulation setup
% MATLAB R2016b + CarSim 2019.0
% Usage: run_carsim

function run_carsim_cruise()
    fprintf('===== CarSim-Simulink Cruise Control =====\n\n');

    myDir = fileparts(mfilename('fullpath'));
    if isempty(which('build_carsim_model'))
        addpath(myDir);
    end

    %% Step 1: Build Simulink model
    fprintf('--- Step 1: Build Simulink model ---\n');
    try
        build_carsim_model();
    catch e
        fprintf('[X] Model build failed: %s\n', e.message);
        return;
    end

    %% Step 2: Launch CarSim
    fprintf('\n--- Step 2: Launch CarSim ---\n');
    csExe = 'C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe';
    csDir = 'C:\Program Files (x86)\CarSim2019.0_Prog';
    if exist(csExe, 'file')
        fprintf('Starting CarSim 2019.0...\n');
        system(['start "" /D "' csDir '" "' csExe '"']);
        fprintf('CarSim launched.\n');
    else
        fprintf('[!] CarSim.exe not found at: %s\n', csExe);
    end

    %% Step 3: Print instructions
    fprintf('\n===== CarSim Setup Steps =====\n');
    print_carsim_steps(myDir);
end

function print_carsim_steps(modelDir)
    fprintf('\n');
    fprintf('1. In CarSim, click [Run Control] tab (top, with play icon)\n\n');
    fprintf('2. Left side Models area:\n');
    fprintf('   - Dropdown: change Internal to Simulink\n');
    fprintf('   - Click browse (...) and select:\n');
    fprintf('     %s\\carsim_cruise_ctrl.slx\n\n', modelDir);
    fprintf('3. Click [I/O Channels] button:\n');
    fprintf('   Export (Simulink->CarSim): Throttle / Brake_MPa / MotorTorque\n');
    fprintf('   Import (CarSim->Simulink): Vx_kmh / Ax_g / EngineRPM\n\n');
    fprintf('4. Set: Time Step = 0.001  Stop Time = 30\n');
    fprintf('5. Click green Run button\n');
    fprintf('------------------------------------------------\n');
end
