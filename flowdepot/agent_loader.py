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


def load_agent(agent_dir: str, agent_config_path: str = '', system_config_path: str = "config/system.yaml"):
    """
    Load an agent using its manifest.yaml and agent.yaml.
    
    Parameters:
        agent_path (str): Path to the agent directory.
        config_path (str): Optional path to a shared default config.

    Returns:
        An instance of the agent class.
    """
    _agent_dir = Path(agent_dir)
    
    manifest_file = _agent_dir / "manifest.yaml"
    # 讀取 manifest.yaml
    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)

    # Merge system.yaml + agent.yaml
    agent_config = {}
    
    # Read system.yaml
    if Path(system_config_path).exists():
        with open(system_config_path, 'r', encoding='utf-8') as f:
            agent_config = yaml.safe_load(f) or {}
            
    # Read agent.yaml
    if not agent_config_path:
        agent_config_path = manifest.get("config_file")
    if agent_config_path:
        _path = _agent_dir / agent_config_path
        if _path.exists():
            with open(_path, 'r', encoding='utf-8') as f:
                agent_cfg = yaml.safe_load(f) or {}
            # agent_config['agent'] = agent_cfg
            agent_config = deep_merge(agent_config, agent_cfg)

    # Load agent instance dynamically.
    agent_instance = None
    entry_point = manifest["entry_point"]
    class_name = manifest["class_name"]

    entry_file = _agent_dir / entry_point
    spec = importlib.util.spec_from_file_location("agent_module", entry_file)
    if spec:
        module = importlib.util.module_from_spec(spec)
        if module and spec.loader is not None:
            spec.loader.exec_module(module)
            agent_class = getattr(module, class_name)
            agent_instance = agent_class(agent_config['name'], agent_config)
    
    return agent_instance
        
