import os


def get_env(key: str) -> str:
    """读取环境变量，支持 macOS 环境变量和 Windows 注册表回退。"""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as reg:
            val, _ = winreg.QueryValueEx(reg, key)
        if val:
            os.environ[key] = val
            return val
    except (OSError, ImportError):
        pass
    raise KeyError(f"{key} 未设置，请配置环境变量或在 bot/.env 文件中设置")
