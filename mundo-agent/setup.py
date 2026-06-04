"""蒙多首次启动向导 — 全量 AI 模型选择"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Tuple

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
MUNDO_ENV = MUNDO_HOME / ".env"
MUNDO_SETUP_FLAG = MUNDO_HOME / ".setup_complete"

G = "\033[38;5;178m"
R = "\033[0m"
D = "\033[2m"
A = "\033[38;5;136m"
OK = "\033[38;5;65m"
ERR = "\033[38;5;131m"
CYAN = "\033[38;5;87m"
STEEL = "\033[38;5;248m"

# ═══════════════════════════════════════════════
# 全量 AI 模型目录
# ═══════════════════════════════════════════════

PROVIDERS = {
    # ─── 中国模型 ───
    "xiaomi": {
        "label": "小米 MiMo",
        "model": "mimo-v2.5-pro",
        "env_key": "XIAOMI_API_KEY",
        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "anthropic_base_url": "https://token-plan-cn.xiaomimimo.com/anthropic",
        "desc": "国产大模型，性价比极高，国内直连",
        "url": "https://xiaoai.mi.com/mimo",
        "region": "cn",
        "group": "中国模型",
    },
    "deepseek": {
        "label": "DeepSeek",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "desc": "国产代码大模型，编码推理顶级，价格低",
        "url": "https://platform.deepseek.com",
        "region": "cn",
        "group": "中国模型",
    },
    "qwen": {
        "label": "阿里通义千问 Qwen",
        "model": "qwen-max",
        "env_key": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "desc": "阿里旗舰模型，多语言能力强",
        "url": "https://dashscope.console.aliyun.com",
        "region": "cn",
        "group": "中国模型",
    },
    "zhipu": {
        "label": "智谱 GLM",
        "model": "glm-4-plus",
        "env_key": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "desc": "清华系，GLM 系列，工具调用强",
        "url": "https://open.bigmodel.cn",
        "region": "cn",
        "group": "中国模型",
    },
    "moonshot": {
        "label": "月之暗面 Kimi",
        "model": "moonshot-v1-128k",
        "env_key": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "desc": "Kimi，128K 长上下文，擅长文档理解",
        "url": "https://platform.moonshot.cn",
        "region": "cn",
        "group": "中国模型",
    },
    "minimax": {
        "label": "MiniMax",
        "model": "MiniMax-Text-01",
        "env_key": "MINIMAX_API_KEY",
        "base_url": "https://api.minimax.chat/v1",
        "desc": "MiniMax 旗舰，长上下文，多模态",
        "url": "https://platform.minimaxi.com",
        "region": "cn",
        "group": "中国模型",
    },
    "baidu": {
        "label": "百度文心 ERNIE",
        "model": "ernie-4.5-8k-preview",
        "env_key": "BAIDU_API_KEY",
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "desc": "百度旗舰，中文理解强",
        "url": "https://cloud.baidu.com/wenxin",
        "region": "cn",
        "group": "中国模型",
    },
    "bytedance": {
        "label": "字节豆包",
        "model": "doubao-pro-32k",
        "env_key": "VOLC_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "desc": "字节跳动豆包大模型，火山引擎托管",
        "url": "https://console.volcengine.com/ark",
        "region": "cn",
        "group": "中国模型",
    },
    "baichuan": {
        "label": "百川智能",
        "model": "Baichuan4",
        "env_key": "BAICHUAN_API_KEY",
        "base_url": "https://api.baichuan-ai.com/v1",
        "desc": "百川大模型，中文创作强",
        "url": "https://platform.baichuan-ai.com",
        "region": "cn",
        "group": "中国模型",
    },
    "yi": {
        "label": "零一万物 Yi",
        "model": "yi-large",
        "env_key": "YI_API_KEY",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "desc": "李开复创办，Yi 系列大模型",
        "url": "https://platform.lingyiwanwu.com",
        "region": "cn",
        "group": "中国模型",
    },
    "stepfun": {
        "label": "阶跃星辰 Step",
        "model": "step-2-16k",
        "env_key": "STEPFUN_API_KEY",
        "base_url": "https://api.stepfun.com/v1",
        "desc": "Step 系列，多模态能力强",
        "url": "https://platform.stepfun.com",
        "region": "cn",
        "group": "中国模型",
    },
    "tencent": {
        "label": "腾讯混元",
        "model": "hunyuan-pro",
        "env_key": "TENCENT_API_KEY",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "desc": "腾讯旗舰，代码和推理能力强",
        "url": "https://cloud.tencent.com/product/hunyuan",
        "region": "cn",
        "group": "中国模型",
    },
    "iflytek": {
        "label": "科大讯飞星火",
        "model": "spark-4.0-ultra",
        "env_key": "SPARK_API_KEY",
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "desc": "讯飞星火，语音+语言多模态",
        "url": "https://xinghuo.xfyun.cn",
        "region": "cn",
        "group": "中国模型",
    },
    "siliconflow": {
        "label": "硅基流动 SiliconFlow",
        "model": "deepseek-ai/DeepSeek-V3",
        "env_key": "SILICONFLOW_API_KEY",
        "base_url": "https://api.siliconflow.cn/v1",
        "desc": "国产模型聚合平台，便宜快速",
        "url": "https://siliconflow.cn",
        "region": "cn",
        "group": "中国模型",
    },

    # ─── 国际模型 ───
    "openai": {
        "label": "OpenAI",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "desc": "GPT-4o / o3 / o4-mini，全球顶级",
        "url": "https://platform.openai.com",
        "region": "intl",
        "group": "国际模型",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "desc": "Claude Opus/Sonnet/Haiku，代码推理顶级",
        "url": "https://console.anthropic.com",
        "region": "intl",
        "group": "国际模型",
    },
    "google": {
        "label": "Google Gemini",
        "model": "gemini-2.5-pro",
        "env_key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "desc": "Gemini 2.5 Pro/Flash，100万上下文",
        "url": "https://aistudio.google.com",
        "region": "intl",
        "group": "国际模型",
    },
    "mistral": {
        "label": "Mistral AI",
        "model": "mistral-large-latest",
        "env_key": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "desc": "Mistral Large/Codestral，欧洲顶级",
        "url": "https://console.mistral.ai",
        "region": "intl",
        "group": "国际模型",
    },
    "groq": {
        "label": "Groq",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "desc": "超快推理，LPU 芯片加速",
        "url": "https://console.groq.com",
        "region": "intl",
        "group": "国际模型",
    },
    "xai": {
        "label": "xAI Grok",
        "model": "grok-3",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "desc": "马斯克旗下，Grok-3 旗舰",
        "url": "https://console.x.ai",
        "region": "intl",
        "group": "国际模型",
    },
    "cohere": {
        "label": "Cohere",
        "model": "command-r-plus",
        "env_key": "COHERE_API_KEY",
        "base_url": "https://api.cohere.com/v2",
        "desc": "Command R+，企业级 RAG 强",
        "url": "https://dashboard.cohere.com",
        "region": "intl",
        "group": "国际模型",
    },
    "huggingface": {
        "label": "Hugging Face",
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "env_key": "HF_TOKEN",
        "base_url": "https://api-inference.huggingface.co/v1",
        "desc": "开源模型推理，Llama/Mistral/Qwen",
        "url": "https://huggingface.co/settings/tokens",
        "region": "intl",
        "group": "国际模型",
    },

    # ─── 聚合平台 ───
    "openrouter": {
        "label": "OpenRouter",
        "model": "anthropic/claude-sonnet-4",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "desc": "100+ 模型聚合，一个 Key 用所有",
        "url": "https://openrouter.ai",
        "region": "global",
        "group": "聚合平台",
    },
    "together": {
        "label": "Together AI",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "env_key": "TOGETHER_API_KEY",
        "base_url": "https://api.together.xyz/v1",
        "desc": "开源模型快速推理，便宜",
        "url": "https://api.together.xyz",
        "region": "intl",
        "group": "聚合平台",
    },
    "fireworks": {
        "label": "Fireworks AI",
        "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "env_key": "FIREWORKS_API_KEY",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "desc": "超快开源模型推理",
        "url": "https://fireworks.ai",
        "region": "intl",
        "group": "聚合平台",
    },
    "deepinfra": {
        "label": "DeepInfra",
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "env_key": "DEEPINFRA_API_KEY",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "desc": "便宜的开源模型托管",
        "url": "https://deepinfra.com",
        "region": "intl",
        "group": "聚合平台",
    },
    "cloudflare": {
        "label": "Cloudflare Workers AI",
        "model": "@cf/meta/llama-3.3-70b-instruct-fp8",
        "env_key": "CLOUDFLARE_API_KEY",
        "base_url": "https://api.cloudflare.com/client/v4/accounts",
        "desc": "边缘推理，免费额度慷慨",
        "url": "https://developers.cloudflare.com/workers-ai",
        "region": "intl",
        "group": "聚合平台",
    },
    "replicate": {
        "label": "Replicate",
        "model": "meta/llama-3.3-70b-instruct",
        "env_key": "REPLICATE_API_TOKEN",
        "base_url": "https://api.replicate.com/v1",
        "desc": "按需运行开源模型，按秒计费",
        "url": "https://replicate.com",
        "region": "intl",
        "group": "聚合平台",
    },
}

# 用于列表展示的顺序
DISPLAY_ORDER = [
    # 中国模型
    "xiaomi", "deepseek", "qwen", "zhipu", "moonshot", "minimax",
    "baidu", "bytedance", "baichuan", "yi", "stepfun", "tencent",
    "iflytek", "siliconflow",
    # 国际模型
    "openai", "anthropic", "google", "mistral", "groq", "xai",
    "cohere", "huggingface",
    # 聚合平台
    "openrouter", "together", "fireworks", "deepinfra", "cloudflare", "replicate",
]


def is_setup_done() -> bool:
    return MUNDO_SETUP_FLAG.exists()


def load_local_env() -> Dict[str, str]:
    env = {}
    # 先加载 hermes .env（作为 fallback）
    hermes_env = Path.home() / ".hermes" / ".env"
    for path in [hermes_env, MUNDO_ENV]:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def save_local_env(key: str, value: str):
    MUNDO_HOME.mkdir(parents=True, exist_ok=True)
    env = load_local_env()
    env[key] = value
    lines = [f"{k}={v}" for k, v in env.items()]
    MUNDO_ENV.write_text("\n".join(lines) + "\n")
    os.environ[key] = value


def mark_setup_done(provider: str, model: str):
    MUNDO_SETUP_FLAG.write_text(f"{provider}\n{model}\n")


def get_saved_provider() -> Optional[str]:
    if not MUNDO_SETUP_FLAG.exists():
        return None
    lines = MUNDO_SETUP_FLAG.read_text().strip().splitlines()
    return lines[0] if lines else None


def get_saved_model() -> Optional[str]:
    if not MUNDO_SETUP_FLAG.exists():
        return None
    lines = MUNDO_SETUP_FLAG.read_text().strip().splitlines()
    return lines[1] if len(lines) > 1 else None


def _display_providers():
    """分组显示所有 provider"""
    groups = {}
    for key in DISPLAY_ORDER:
        p = PROVIDERS[key]
        g = p["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append((key, p))

    idx = 1
    index_map = {}
    for group_name, items in groups.items():
        print(f"\n  {A}━━ {group_name} ━━{R}")
        for key, p in items:
            has_key = bool(load_local_env().get(p["env_key"], ""))
            tag = f"{OK}✓ 已配置{R}" if has_key else f"{D}未配置{R}"
            print(f"    {G}[{idx:2d}]{R} {p['label']:28} {D}{p['desc']}{R}  {tag}")
            index_map[str(idx)] = key
            idx += 1

    return index_map


def run_setup() -> Tuple[str, str]:
    print(f"""
{G}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              👑 蒙多首次启动设置                           ║
║                                                          ║
║         选择你的 AI 模型，输入 API Key                     ║
║         Key 仅保存在本地，不会上传到任何地方                 ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{R}
""")

    index_map = _display_providers()

    print(f"\n  {D}输入编号选择，输入名称搜索，回车跳过{R}\n")

    while True:
        choice = input(f"  {G}选择模型：{R}").strip()
        if not choice:
            print(f"  {D}跳过设置，使用默认配置{R}")
            return "xiaomi", "mimo-v2.5-pro"

        # 数字选择
        if choice in index_map:
            selected_key = index_map[choice]
            break

        # 名称搜索
        matches = []
        for key, p in PROVIDERS.items():
            if choice.lower() in key.lower() or choice.lower() in p["label"].lower():
                matches.append((key, p))

        if len(matches) == 1:
            selected_key = matches[0][0]
            break
        elif len(matches) > 1:
            print(f"  {A}找到 {len(matches)} 个匹配：{R}")
            for key, p in matches:
                print(f"    {G}{key}{R}: {p['label']}")
            print(f"  {D}请输入具体名称{R}")
            continue
        else:
            print(f"  {ERR}未找到 '{choice}'，请重试{R}")
            continue

    selected = PROVIDERS[selected_key]
    print(f"\n  {OK}✓ 选择：{selected['label']} ({selected['model']}){R}")

    env = load_local_env()
    existing_key = env.get(selected["env_key"], "")
    if existing_key:
        masked = existing_key[:8] + "..." + existing_key[-4:] if len(existing_key) > 12 else "***"
        print(f"  {D}已有 Key: {masked}{R}")
        reuse = input(f"  {G}继续使用已有 Key？[Y/n]：{R}").strip().lower()
        if reuse != "n":
            mark_setup_done(selected_key, selected["model"])
            return selected_key, selected["model"]

    print(f"\n  {A}获取 Key → {selected['url']}{R}")
    print(f"  {D}Key 仅保存在 ~/.hermes/mundo-agent/.env{R}\n")

    while True:
        api_key = input(f"  {G}输入 API Key：{R}").strip()
        if not api_key:
            print(f"  {ERR}Key 不能为空{R}")
            continue
        if len(api_key) < 10:
            print(f"  {ERR}Key 太短，请检查{R}")
            continue
        break

    save_local_env(selected["env_key"], api_key)
    mark_setup_done(selected_key, selected["model"])

    masked = api_key[:8] + "..." + api_key[-4:]
    print(f"\n  {OK}✓ Key 已保存：{masked}{R}")
    print(f"  {OK}✓ 模型已设置：{selected_key}/{selected['model']}{R}")

    # 多模型协同选择
    print(f"\n  {A}━━ 多模型协同 ━━{R}")
    print(f"  {D}蒙多支持同时接入多个 AI 模型，根据任务类型智能分配。{R}")
    print(f"  {D}例如：DeepSeek 写代码 + MiMo 日常对话 + Claude 深度推理{R}")
    print(f"  {D}不添加也能用，蒙多会用分身模式。{R}\n")

    add_more = input(f"  {G}要添加更多模型吗？[y/N]：{R}").strip().lower()
    collab_count = 0
    if add_more == "y":
        print(f"\n  {D}输入要添加的模型编号（用空格分隔，如 2 15 23）：{R}")
        print(f"  {D}输入 0 结束添加{R}\n")
        index_map = _display_providers()

        while True:
            choices = input(f"\n  {G}模型编号（空格分隔，0 结束）：{R}").strip()
            if choices == "0" or not choices:
                break

            for c in choices.split():
                c = c.strip()
                if c == "0":
                    break
                if c in index_map:
                    pk = index_map[c]
                    p = PROVIDERS[pk]
                    # 检查是否已有 key
                    existing = load_local_env().get(p["env_key"], "")
                    if existing:
                        print(f"  {OK}  ✓ {p['label']}（已有 Key）{R}")
                        collab_count += 1
                        continue
                    print(f"\n  {A}  {p['label']} — 获取 Key: {p['url']}{R}")
                    k = input(f"  {G}  输入 Key：{R}").strip()
                    if k and len(k) >= 10:
                        save_local_env(p["env_key"], k)
                        print(f"  {OK}  ✓ {p['label']} 已添加{R}")
                        collab_count += 1
                    else:
                        print(f"  {D}  跳过{R}")
                else:
                    print(f"  {ERR}  无效编号: {c}{R}")

    total = 1 + collab_count
    print(f"\n  {OK}✓ 设置完成！共 {total} 个模型就绪。{R}")
    if total >= 3:
        print(f"  {G}  蒙多将根据任务类型智能分配模型。{R}")
    elif total == 2:
        print(f"  {G}  两个模型协同，主模型处理任务，辅助模型验证。{R}")
    print()

    return selected_key, selected["model"]


def add_provider_interactive():
    print(f"\n  {A}添加新 AI 模型{R}\n")
    index_map = _display_providers()
    print()

    choice = input(f"  {G}选择编号或名称：{R}").strip()
    if choice in index_map:
        selected_key = index_map[choice]
    elif choice in PROVIDERS:
        selected_key = choice
    else:
        print(f"  {ERR}无效选择{R}")
        return None, None

    selected = PROVIDERS[selected_key]
    print(f"\n  {A}获取 Key → {selected['url']}{R}")
    api_key = input(f"  {G}输入 API Key：{R}").strip()
    if not api_key:
        print(f"  {ERR}取消{R}")
        return None, None

    save_local_env(selected["env_key"], api_key)
    print(f"  {OK}✓ {selected['label']} 已添加{R}")
    return selected_key, selected["model"]
