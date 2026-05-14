function y = lowpass_filter(x, fc, fs)
% 一阶低通滤波器
% 输入：
%   x  - 输入信号
%   fc - 截止频率 [Hz]
%   fs - 采样频率 [Hz]
% 输出：
%   y  - 滤波后信号
%
% R2016b 兼容

    if fc <= 0 || fc >= fs/2
        error('截止频率需在 0 ~ fs/2 之间');
    end

    tau = 1 / (2 * pi * fc);       % 时间常数
    dt  = 1 / fs;
    alpha = dt / (tau + dt);        % 滤波系数

    y = zeros(size(x));
    y(1) = x(1);

    for k = 2:length(x)
        y(k) = (1 - alpha) * y(k-1) + alpha * x(k);
    end
end
