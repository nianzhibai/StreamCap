import os

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def get_env_bool(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def apply_user_config_env_overrides(user_config: dict) -> dict:
    config = user_config.copy()
    login_required = get_env_bool("LOGIN_REQUIRED")
    if login_required is not None:
        config["login_required"] = login_required
    return config
