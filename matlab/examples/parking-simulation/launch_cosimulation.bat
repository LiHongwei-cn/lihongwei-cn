@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   CarSim + Simulink 倒车入库联合仿真 一键启动
echo   CarSim 2019.0 + MATLAB R2016b
echo ============================================================
echo.

cd /d "%~dp0"
echo 工作目录: %CD%
echo.

REM === 路径配置 ===
set "MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe"
set "CARSIM_EXE=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe"
set "SCRIPT_DIR=%CD%"
set "CPAR_FILE=%SCRIPT_DIR%\Parking_Reversing.cpar"
set "SFUNCTION_SRC=C:\Program Files (x86)\CarSim2019.0_Prog\Programs\vs_connect\vs_connect_sf2.mexw64"
set "SFUNCTION_DST=%SCRIPT_DIR%\vs_connect_sf2.mexw64"

REM === 检查依赖 ===
echo [检查] 验证所有必需文件...
echo.

if not exist "%MATLAB_EXE%" (
    echo [错误] MATLAB未找到: %MATLAB_EXE%
    pause
    exit /b 1
)
echo   [OK] MATLAB R2016b

if not exist "%CARSIM_EXE%" (
    echo [错误] CarSim未找到: %CARSIM_EXE%
    pause
    exit /b 1
)
echo   [OK] CarSim 2019.0

if not exist "%CPAR_FILE%" (
    echo [错误] CPAR配置文件未找到: %CPAR_FILE%
    pause
    exit /b 1
)
echo   [OK] CPAR配置文件: Parking_Reversing.cpar

if not exist "%SFUNCTION_SRC%" (
    echo [警告] S-Function MEX文件未找到，需要从CarSim导出
    set "NEED_EXPORT=1"
) else (
    echo   [OK] S-Function MEX文件
    set "NEED_EXPORT=0"
)

echo.

REM === 步骤1: 复制S-Function到工作目录 ===
echo [步骤1/5] 准备S-Function文件...
if "%NEED_EXPORT%"=="0" (
    if not exist "%SFUNCTION_DST%" (
        copy "%SFUNCTION_SRC%" "%SFUNCTION_DST%" >nul
        echo   - 已复制S-Function到工作目录
    ) else (
        echo   - S-Function已存在于工作目录
    )
) else (
    echo   - 需要从CarSim导出S-Function（稍后操作）
)
echo.

REM === 步骤2: 打开CarSim ===
echo [步骤2/5] 启动CarSim 2019.0...
start "" "%CARSIM_EXE%"
echo   - CarSim正在启动...
echo   - 等待10秒让CarSim完全加载...
timeout /t 10 /nobreak >nul
echo   - CarSim已启动
echo.

REM === 步骤3: 显示CarSim操作指引 ===
echo [步骤3/5] CarSim操作指引
echo.
echo   ============================================================
echo   请在CarSim中完成以下操作：
echo   ============================================================
echo.
echo   1. 导入数据集：
echo      File ^> Import Dataset
echo      选择: %CPAR_FILE%
echo      点击 OK 确认导入
echo.
echo   2. 导出S-Function（如果步骤1未复制成功）：
echo      Settings ^> Simulink / MATLAB
echo      点击 "Export S-Function"
echo      保存到: %SCRIPT_DIR%\
echo.
echo   3. 确认仿真设置：
echo      - 确保仿真时间 >= 60秒
echo      - 确保Simulink接口已启用
echo.
echo   ============================================================
echo.

REM === 步骤4: 等待用户完成CarSim操作 ===
echo [步骤4/5] 等待CarSim配置完成...
echo.
echo   完成上述CarSim操作后，按任意键继续启动MATLAB...
echo.
pause

REM === 步骤5: 启动MATLAB ===
echo [步骤5/5] 启动MATLAB R2016b...
echo.

REM 创建MATLAB启动脚本
set "MATLAB_SCRIPT=%SCRIPT_DIR%\temp_launch.m"
(
echo %% 倒车入库联合仿真 - 自动启动脚本
echo cd '%SCRIPT_DIR%';
echo.
echo fprintf('========================================\n'^);
echo fprintf('  倒车入库 CarSim+Simulink 联合仿真\n'^);
echo fprintf('========================================\n\n'^);
echo.
echo %% 添加CarSim S-Function路径
echo carsim_mex_dir = 'C:\Program Files (x86)\CarSim2019.0_Prog\Programs\vs_connect';
echo if exist(carsim_mex_dir, 'dir'^)
echo     addpath(carsim_mex_dir^);
echo     fprintf('已添加CarSim S-Function路径\n'^);
echo end
echo.
echo %% 添加工作目录
echo addpath('%SCRIPT_DIR%'^);
echo.
echo %% 检查S-Function
echo if exist('vs_connect_sf2.mexw64', 'file'^)
echo     fprintf('S-Function: vs_connect_sf2.mexw64 [OK]\n'^);
echo elseif exist('sf_car_sim.mexw64', 'file'^)
echo     fprintf('S-Function: sf_car_sim.mexw64 [OK]\n'^);
echo else
echo     fprintf('警告: 未找到S-Function MEX文件\n'^);
echo     fprintf('请确保已从CarSim导出S-Function\n'^);
echo end
echo.
echo fprintf('\n准备就绪。运行仿真请执行:\n'^);
echo fprintf('  run_parking_simulation\n\n'^);
echo.
echo %% 询问是否立即运行
echo answer = input('是否立即运行联合仿真？(y/n): ', 's'^);
echo if strcmpi(answer, 'y'^) ^|^| strcmpi(answer, 'yes'^)
echo     fprintf('\n正在运行联合仿真...\n\n'^);
echo     try
echo         run_parking_simulation;
echo     catch ME
echo         fprintf('仿真错误: %s\n', ME.message^);
echo         fprintf('请检查CarSim是否已正确导入数据集\n'^);
echo     end
echo end
) > "%MATLAB_SCRIPT%"

echo   正在启动MATLAB...
start "" "%MATLAB_EXE%" -r "run('%MATLAB_SCRIPT%')"
echo   - MATLAB正在启动...
echo.

echo ============================================================
echo   所有程序已启动！
echo ============================================================
echo.
echo   运行流程：
echo   1. CarSim 已打开 - 请导入CPAR文件
echo   2. MATLAB 已打开 - 等待运行仿真
echo   3. 完成CarSim配置后，在MATLAB中运行:
echo      run_parking_simulation
echo.
echo   如果遇到问题：
echo   - 检查CarSim是否已导入Parking_Reversing.cpar
echo   - 检查S-Function是否在工作目录中
echo   - 检查MATLAB路径是否包含工作目录
echo.
echo ============================================================
echo.
echo 按任意键退出此窗口（CarSim和MATLAB将继续运行）...
pause >nul

REM 清理临时文件
if exist "%MATLAB_SCRIPT%" del "%MATLAB_SCRIPT%"
