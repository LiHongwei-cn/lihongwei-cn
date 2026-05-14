function val = rms_calculation(signal)
% 计算均方根值 (RMS)
% 输入：
%   signal - 输入信号向量
% 输出：
%   val    - RMS 值
%
% R2016b 兼容

    if isempty(signal)
        val = 0;
        return;
    end

    N = length(signal);
    val = sqrt(sum(signal.^2) / N);
end
