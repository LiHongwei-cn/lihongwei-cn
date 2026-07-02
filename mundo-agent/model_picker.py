"""蒙多模型选择器 v2.3.1 — 交互式 Provider + 版本切换

两级菜单：先选 Provider，再选模型版本（如 DeepSeek V4 / V4-Pro / R1）。
支持 API Key 配置与已配置模型快速切换。
"""

from typing import Dict, List, Optional, Tuple

from setup import (
    PROVIDERS, DISPLAY_ORDER, load_local_env, save_local_env,
    mark_setup_done, get_saved_provider, get_saved_model,
)
from model_profiles import PROVIDER_DATABASE, SmartModelSelector


def get_provider_models(provider_id: str) -> List[Dict]:
    """获取 provider 下所有可选模型版本"""
    db = PROVIDER_DATABASE.get(provider_id)
    if db and db.models:
        items = []
        for mid, spec in db.models.items():
            items.append({
                "id": mid,
                "name": spec.name,
                "strengths": ", ".join(spec.strengths[:3]),
                "tier": spec.capability_tier,
                "cache": "✓缓存" if spec.supports_caching else "",
            })
        return items

    cfg = PROVIDERS.get(provider_id, {})
    default = cfg.get("model", "")
    if default:
        return [{"id": default, "name": default, "strengths": cfg.get("desc", ""), "tier": "default", "cache": ""}]
    return []


def get_model_display_name(provider_id: str, model_id: str) -> str:
    spec = SmartModelSelector.get_model_info(provider_id, model_id)
    if spec:
        return spec.name
    cfg = PROVIDERS.get(provider_id, {})
    return model_id or cfg.get("model", "unknown")


def list_configured_providers() -> List[str]:
    env = load_local_env()
    configured = []
    for key, cfg in PROVIDERS.items():
        if env.get(cfg.get("env_key", "")):
            configured.append(key)
    return configured


def _print_header(title: str):
    from display import console
    console.print(f"\n  [gold]━━ {title} ━━[/]")


def _read_choice(prompt: str = "选择") -> str:
    from display import console
    try:
        return input(f"  {prompt}：").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def pick_provider(prefer_configured: bool = True) -> Optional[str]:
    """第一级：选择 Provider"""
    from display import console

    configured = set(list_configured_providers())
    _print_header("选择 AI 模型提供商")
    console.print("  [dim]输入编号或名称，回车取消[/]\n")

    index_map: Dict[str, str] = {}
    idx = 1
    current_group = ""
    for key in DISPLAY_ORDER:
        if key not in PROVIDERS:
            continue
        p = PROVIDERS[key]
        if p["group"] != current_group:
            current_group = p["group"]
            console.print(f"\n  [gold.dim]── {current_group} ──[/]")
        has_key = key in configured
        tag = "[ok]✓[/]" if has_key else "[dim]○[/]"
        cur = " [gold]← 当前[/]" if key == get_saved_provider() else ""
        console.print(f"  {tag} [gold][{idx:2d}][/] {p['label']:22} [dim]{p['desc'][:28]}[/]{cur}")
        index_map[str(idx)] = key
        idx += 1

    choice = _read_choice()
    if not choice:
        return None
    if choice in index_map:
        return index_map[choice]
    if choice in PROVIDERS:
        return choice
    matches = [k for k in PROVIDERS if choice.lower() in k.lower()
               or choice.lower() in PROVIDERS[k]["label"].lower()]
    if len(matches) == 1:
        return matches[0]
    console.print(f"  [err]未找到: {choice}[/]")
    return None


def pick_model_variant(provider_id: str) -> Optional[str]:
    """第二级：选择模型版本"""
    from display import console

    models = get_provider_models(provider_id)
    if not models:
        return PROVIDERS.get(provider_id, {}).get("model")

    if len(models) == 1:
        return models[0]["id"]

    p = PROVIDERS.get(provider_id, {})
    _print_header(f"{p.get('label', provider_id)} — 选择版本")
    console.print("  [dim]选择模型版本[/]\n")

    saved = get_saved_model()
    for i, m in enumerate(models, 1):
        cur = " [gold]← 当前[/]" if m["id"] == saved else ""
        cache = f" [dim]{m['cache']}[/]" if m["cache"] else ""
        console.print(
            f"  [gold][{i}][/] {m['name']:22} [dim]{m['id']}{cache}[/]"
            f"  [dim]{m['strengths'][:30]}[/]{cur}"
        )

    choice = _read_choice("版本编号")
    if not choice:
        return PROVIDERS.get(provider_id, {}).get("model")
    if choice.isdigit():
        n = int(choice)
        if 1 <= n <= len(models):
            return models[n - 1]["id"]
    for m in models:
        if choice.lower() in m["id"].lower() or choice.lower() in m["name"].lower():
            return m["id"]
    console.print(f"  [err]无效选择，使用默认模型[/]")
    return PROVIDERS.get(provider_id, {}).get("model")


def ensure_api_key(provider_id: str) -> bool:
    """确保 Provider 有 API Key，没有则引导输入"""
    from display import console

    cfg = PROVIDERS.get(provider_id)
    if not cfg:
        return False

    env = load_local_env()
    existing = env.get(cfg["env_key"], "")
    if existing:
        masked = existing[:8] + "..." + existing[-4:] if len(existing) > 12 else "***"
        console.print(f"  [dim]已有 Key: {masked}[/]")
        reuse = _read_choice("继续使用已有 Key？[Y/n]")
        if reuse.lower() != "n":
            return True

    console.print(f"\n  [gold.dim]获取 Key → {cfg['url']}[/]")
    console.print(f"  [dim]Key 保存在 ~/.hermes/mundo-agent/.env[/]\n")

    while True:
        api_key = _read_choice("输入 API Key")
        if not api_key:
            console.print("  [err]取消配置[/]")
            return False
        if len(api_key) < 10:
            console.print("  [err]Key 太短，请检查[/]")
            continue
        save_local_env(cfg["env_key"], api_key)
        console.print(f"  [ok]✓ Key 已保存[/]")
        return True


def run_model_picker(current_provider: str = None, current_model: str = None) -> Optional[Tuple[str, str]]:
    """完整模型切换流程：Provider → 版本 → API Key"""
    from display import console

    provider = pick_provider()
    if not provider:
        console.print("  [dim]已取消[/]")
        return None

    model = pick_model_variant(provider)
    if not ensure_api_key(provider):
        return None

    mark_setup_done(provider, model)
    label = get_model_display_name(provider, model)
    console.print(f"\n  [ok]✓ 已切换至 {PROVIDERS[provider]['label']} / {label}[/]")
    console.print(f"  [dim]  API 模型 ID: {model}[/]\n")
    return provider, model


def format_status_model(provider: str, model: str) -> str:
    """状态栏模型显示"""
    name = get_model_display_name(provider, model)
    if len(name) > 18:
        return name[:15] + "..."
    return name
