# R2016b 兼容性速查表

MATLAB R2016b 是用户的兼容性底线。生成代码时必须检查以下禁止项。

## 禁止使用的函数

| 禁止 | 替代方案 | 版本 |
|------|----------|------|
| `rms()` | `sqrt(mean(x.^2))` | R2017a+ |
| `arguments` 块 | `nargin` 检查 | R2019b+ |
| `string` 类型 | `char` 类型 | R2016b+ 但避免 |
| `tiledlayout` / `nexttile` | `subplot` | R2019b+ |
| `readtable` / `writetable` | `csvread` / `csvwrite` | R2019a+ |
| `readmatrix` / `writematrix` | `csvread` / `csvwrite` | R2019a+ |
| `datetime` | `datenum` / `datestr` | R2014b+ 但避免 |
| `str2double` 替代 `str2num` | 可用，但 `str2num` 内部用 eval | - |
| `clear all` | `clearvars` | - |
| `eval` / `evalc` / `evalin` | 动态字段名 `s.(name)` | 禁止 |
| `arguments` 验证 | `nargin` + `validateattributes` | R2019b+ |

## 禁止使用的语法

| 禁止 | 说明 |
|------|------|
| 隐式展开 `A + B`（维度不同） | R2016b+ 支持但为兼容性避免 |
| `arguments...end` 验证块 | R2019b+ |
| 嵌套函数中的 `end` 关键字 | 某些情况不兼容 |
| `string` 字面量 `"text"` | 用 `'text'` |

## Simulink API（R2016b 可用）

```matlab
% 可用
new_system / open_system / save_system
add_block / add_line / delete_block / delete_line
set_param / get_param
bdIsLoaded / close_system
sim()

% 禁止（R2018a+）
Simulink.ModelAdvisor
sltest.testmanager
```

## 代码生成检查清单

生成 MATLAB 代码后，自动检查：
- [ ] 无 `rms()` 调用
- [ ] 无 `arguments` 块
- [ ] 无 `string` 类型（用 `char`）
- [ ] 无 `tiledlayout` / `nexttile`（用 `subplot`）
- [ ] 无 `readtable` / `writetable`（用 `csvread` / `csvwrite`）
- [ ] 无 `datetime`（用 `datenum`）
- [ ] 无 `eval` / `evalin`
- [ ] 数值单位在注释中标注：`[Ohm]`、`[rad/s]`、`[rpm]`
- [ ] 前向欧拉法有注释说明
- [ ] 函数 <200 行
