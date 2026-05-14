function [freq, mag] = fft_analysis(signal, fs)
% FFT 频谱分析
% 输入：
%   signal - 时域信号
%   fs     - 采样频率 [Hz]
% 输出：
%   freq   - 频率向量 [Hz]
%   mag    - 幅值
%
% R2016b 兼容

    N = length(signal);
    if N < 2
        freq = 0; mag = 0;
        return;
    end

    Y = fft(signal);
    P2 = abs(Y / N);
    P1 = P2(1:floor(N/2)+1);
    P1(2:end-1) = 2 * P1(2:end-1);

    freq = fs * (0:floor(N/2)) / N;
    mag  = P1;
end
