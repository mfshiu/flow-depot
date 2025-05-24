import yaml
import importlib.util
from pathlib import Path
from copy import deepcopy



def deep_merge(dict1, dict2):
    """Recursively merge dict2 into dict1."""
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_agent(agent_dir: str, default_config_path: str = "config/default.yaml"):
    """
    Load an agent using its manifest.yaml and config.yaml.
    
    Parameters:
        agent_path (str): Path to the agent directory.
        config_path (str): Optional path to a shared default config.

    Returns:
        An instance of the agent class.
    """
    agent_dir = Path(agent_dir)
    manifest_file = agent_dir / "manifest.yaml"

    # 讀取 manifest.yaml
    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)

    entry_point = manifest["entry_point"]
    class_name = manifest["class_name"]

    # 合併 default.yaml + config.yaml
    config = {}
    
    # 讀取 default.yaml
    if Path(default_config_path).exists():
        with open(default_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            
    # 讀取 config.yaml
    config_file = manifest.get("config_file")
    if config_file:
        agent_cfg_path = agent_dir / config_file
        if agent_cfg_path.exists():
            with open(agent_cfg_path, 'r', encoding='utf-8') as f:
                agent_cfg = yaml.safe_load(f) or {}
            config = deep_merge(config, agent_cfg)

    # 動態載入 agent class
    entry_file = agent_dir / entry_point
    spec = importlib.util.spec_from_file_location("agent_module", entry_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    agent_class = getattr(module, class_name)

    return agent_class(manifest["name"], config)
