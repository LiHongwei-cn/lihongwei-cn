"""蒙多 Claude Code 集成 v2 — Token 优化版

解决的问题：
1. Claude Code 添加多余文本导致 token 浪费
2. 任务跑偏（Claude Code 添加解释性文字）
3. 系统提示过长

优化策略：
- --bare 模式：跳过 hooks, LSP, plugin sync, auto-memory 等
- --output-format text：纯文本输出，无 markdown
- --effort medium：适中努力级别，平衡质量和速度
- --exclude-dynamic-system-prompt-sections：减少系统提示
- 输出清理：移除常见多余文本模式
"""

import os
import re
import shutil
import subprocess


# 常见多余文本模式（Claude Code 会添加的）
NOISE_PATTERNS = [
    # 开头解释
    r"^(I'll|I will|Let me|Here's|Here is|Now I|Now let me).*?\n\n",
    # 结尾总结
    r"\n\n(The file|The code|I've|I have|This|Done|Complete|Finished).*?$",
    # 思考过程
    r"\n\n?(Thinking|Let me think|I need to|First,|Firstly,).*?\n\n",
    # 任务描述重复
    r"^(Based on|According to|Given).*?\n\n",
    # 文件操作说明
    r"\n\n?(Creating|Reading|Writing|Editing|Modifying|Updating).*?file.*?\n",
    # 命令执行说明
    r"\n\n?(Running|Executing|Installing|Building).*?\n",
    # 错误处理说明
    r"\n\n?(Error|Failed|Unable to|Cannot).*?\n",
    # 成功确认
    r"\n\n?(Success|Successfully|Done|Complete|Finished).*?\n",
    # 代码块前后说明
    r"\n\n?(Here's the|Below is|The following is).*?code.*?\n",
]

# 编译正则表达式
NOISE_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in NOISE_PATTERNS]


def _clean_output(text: str) -> str:
    """清理 Claude Code 输出，移除多余文本"""
    if not text:
        return text
    
    # 移除常见噪声模式
    for pattern in NOISE_RE:
        text = pattern.sub("", text)
    
    # 移除多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # 移除首尾空白
    text = text.strip()
    
    return text


class ClaudeCodeAgent:
    """Claude Code CLI 封装 — Token 优化版"""

    def __init__(self):
        self.cmd = shutil.which("claude")

    def is_available(self) -> bool:
        return self.cmd is not None

    def exec_full_power(self, prompt: str, workdir: str = None, 
                        clean_output: bool = True,
                        effort: str = "medium") -> str:
        """全力模式执行 Claude Code（Token 优化版）
        
        Args:
            prompt: 任务提示
            workdir: 工作目录
            clean_output: 是否清理输出（移除多余文本）
            effort: 努力级别 (low/medium/high/xhigh/max)
        """
        if not self.is_available():
            return "[Claude Code 未安装]"

        # 构建命令 — Token 优化参数
        cmd = [
            self.cmd,
            "-p", prompt,
            "--dangerously-skip-permissions",
            "--bare",  # 最小模式：跳过 hooks, LSP, plugin sync 等
            "--output-format", "text",  # 纯文本输出
            "--effort", effort,  # 努力级别
            "--exclude-dynamic-system-prompt-sections",  # 减少系统提示
            "--no-markdown",  # 禁用 markdown 格式
        ]
        
        env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=600, cwd=workdir, env=env,
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if clean_output:
                    output = _clean_output(output)
                return output
            
            error = result.stderr.strip()[:500]
            return f"[Claude Code 退出码 {result.returncode}] {error}"
            
        except subprocess.TimeoutExpired:
            return "[Claude Code 超时 (600s)]"
        except Exception as e:
            return f"[Claude Code 异常: {e}]"

    def exec_minimal(self, prompt: str, workdir: str = None) -> str:
        """最小模式执行 — 最大程度减少 token"""
        return self.exec_full_power(
            prompt, 
            workdir=workdir, 
            clean_output=True,
            effort="low"
        )

    def exec_precise(self, prompt: str, workdir: str = None) -> str:
        """精确模式执行 — 适合代码生成"""
        # 添加明确指令，减少多余输出
        precise_prompt = f"""请直接完成以下任务，不要添加任何解释、说明或总结。
只输出代码或结果，不要有多余的文本。

任务：{prompt}"""
        
        return self.exec_full_power(
            precise_prompt, 
            workdir=workdir, 
            clean_output=True,
            effort="medium"
        )

    def exec_code_only(self, prompt: str, workdir: str = None) -> str:
        """纯代码模式 — 只输出代码"""
        code_prompt = f"""只输出代码，不要有任何解释、注释或说明。
如果需要多行代码，直接输出代码块。
不要使用 markdown 格式。

任务：{prompt}"""
        
        return self.exec_full_power(
            code_prompt, 
            workdir=workdir, 
            clean_output=True,
            effort="medium"
        )
