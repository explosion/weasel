import os

from ..schemas import SpacyEnvVars


class ENV_VARS:
    CONFIG_OVERRIDES = "WEASEL_CONFIG_OVERRIDES"


def check_spacy_env_vars():
    SpacyEnvVars().check()


def check_bool_env_var(env_var: str) -> bool:
    """Convert the value of an environment variable to a boolean. Add special
    check for "0" (falsy) and consider everything else truthy, except unset.

    env_var (str): The name of the environment variable to check.
    RETURNS (bool): Its boolean value.
    """
    value = os.environ.get(env_var, False)
    if value == "0":
        return False
    return bool(value)
