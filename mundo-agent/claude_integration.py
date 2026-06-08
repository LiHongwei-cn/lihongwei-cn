"""蒙多 Claude Code 集成 v3 — Token 优化 + 上下文压缩版

解决的问题：
1. Claude Code 添加多余文本导致 token 浪费
2. 任务跑偏（Claude Code 添加解释性文字）
3. 系统提示过长
4. 上下文过长导致 token 浪费

优化策略：
- --bare 模式：跳过 hooks, LSP, plugin sync, auto-memory 等
- --output-format text：纯文本输出，无 markdown
- --effort medium：适中努力级别，平衡质量和速度
- --exclude-dynamic-system-prompt-sections：减少系统提示
- 输出清理：移除常见多余文本模式
- 上下文压缩：自动压缩用户消息，减少 token 消耗
- 智能路由：根据任务复杂度选择努力级别
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
    # 中文思考过程
    r"\n\n?(让我思考|我需要|首先,|第一步).*?\n\n",
    # 中文任务描述
    r"^(根据|基于|按照).*?\n\n",
    # 中文文件操作
    r"\n\n?(创建|读取|写入|编辑|修改|更新).*?文件.*?\n",
    # 中文命令执行
    r"\n\n?(运行|执行|安装|构建).*?\n",
    # 中文错误处理
    r"\n\n?(错误|失败|无法|不能).*?\n",
    # 中文成功确认
    r"\n\n?(成功|完成|完成).*?\n",
]

# 编译正则表达式
NOISE_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in NOISE_PATTERNS]


def _compress_context(text: str) -> str:
    """压缩上下文，减少 token 消耗"""
    if not text:
        return text
    
    # 移除多余空白行
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # 移除行尾空白
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    
    # 移除注释（但保留代码中的注释）
    # 只移除独立行的注释，不移除代码行内的注释
    lines = text.split('\n')
    compressed_lines = []
    for line in lines:
        # 如果是纯注释行（以 // 或 # 开头），且不在代码块内，跳过
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('#'):
            # 检查是否在代码块内（简单判断：行首有缩进）
            if not line.startswith('    ') and not line.startswith('\t'):
                continue
        compressed_lines.append(line)
    
    return '\n'.join(compressed_lines)


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


def _smart_effort(prompt: str) -> str:
    """根据任务复杂度选择努力级别"""
    prompt_lower = prompt.lower()
    
    # 简单任务关键词
    simple_keywords = ['read', 'list', 'show', 'find', 'search', 'check', 'get', 'cat', 'ls', 'grep']
    # 复杂任务关键词
    complex_keywords = ['refactor', 'redesign', 'architect', 'optimize', 'performance', 'security', 'database', 'migration', 'deploy', 'ci/cd', 'pipeline']
    
    # 计算关键词匹配
    simple_score = sum(1 for kw in simple_keywords if kw in prompt_lower)
    complex_score = sum(1 for kw in complex_keywords if kw in prompt_lower)
    
    # 根据长度和关键词判断
    if len(prompt) < 100 and simple_score > 0:
        return "low"
    elif len(prompt) > 500 or complex_score > 0:
        return "high"
    else:
        return "medium"


class ClaudeCodeAgent:
    """Claude Code CLI 封装 — Token 优化 + 上下文压缩版"""

    def __repr__(self) -> str:
        return f"ClaudeCodeAgent(available={self.is_available()})"

    def __init__(self):
        self.cmd = shutil.which("claude")

    def is_available(self) -> bool:
        return self.cmd is not None

    def exec_full_power(self, prompt: str, workdir: str = None,
                        clean_output: bool = True,
                        effort: str = "medium",
                        compress: bool = True,
                        timeout: int = 600) -> str:
        """全力模式执行 Claude Code（Token 优化版）

        Args:
            prompt: 任务提示
            workdir: 工作目录
            clean_output: 是否清理输出（移除多余文本）
            effort: 努力级别 (low/medium/high/xhigh/max)
            compress: 是否压缩上下文（减少 token 消耗）
            timeout: 超时秒数（默认 600）
        """
        if not self.is_available():
            return "[Claude Code 未安装]"

        # 压缩上下文
        if compress:
            prompt = _compress_context(prompt)

        # 构建命令 — Token 优化参数
        cmd = [
            self.cmd,
            "-p", prompt,
            "--dangerously-skip-permissions",
            "--bare",  # 最小模式：跳过 hooks, LSP, plugin sync 等
            "--output-format", "text",  # 纯文本输出
            "--effort", effort,  # 努力级别
            "--exclude-dynamic-system-prompt-sections",  # 减少系统提示
        ]

        env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=workdir, env=env,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if clean_output:
                    output = _clean_output(output)
                return output

            error = result.stderr.strip()[:500]
            return f"[Claude Code 退出码 {result.returncode}] {error}"

        except subprocess.TimeoutExpired:
            return f"[Claude Code 超时 ({timeout}s)]"
        except Exception as e:
            return f"[Claude Code 异常: {e}]"

    def exec_minimal(self, prompt: str, workdir: str = None) -> str:
        """最小模式执行 — 最大程度减少 token"""
        return self.exec_full_power(
            prompt,
            workdir=workdir,
            clean_output=True,
            effort="low",
            compress=True
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
            effort="medium",
            compress=True
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
            effort="medium",
            compress=True
        )

    def exec_smart(self, prompt: str, workdir: str = None, timeout: int = 600) -> str:
        """智能模式 — 根据任务复杂度自动选择努力级别"""
        effort = _smart_effort(prompt)
        
        return self.exec_full_power(
            prompt,
            workdir=workdir,
            clean_output=True,
            effort=effort,
            compress=True,
            timeout=timeout,
        )

    def exec_with_retry(self, prompt: str, workdir: str = None,
                        max_retries: int = 2, timeout: int = 600) -> str:
        """带重试的执行模式"""
        for attempt in range(max_retries + 1):
            try:
                result = self.exec_full_power(
                    prompt,
                    workdir=workdir,
                    clean_output=True,
                    effort="medium",
                    compress=True,
                    timeout=timeout,
                )
                
                # 如果结果包含错误信息，重试
                if result.startswith("[Claude Code") and attempt < max_retries:
                    continue
                
                return result
                
            except Exception as e:
                if attempt < max_retries:
                    continue
                return f"[Claude Code 重试失败: {e}]"
        
        return "[Claude Code 重试耗尽]"
