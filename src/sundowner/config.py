"""Load YAML-based config into the global namespace."""

import yaml


cfg = None
def init(config_filepath):
    global cfg
    with open(config_filepath) as f:
        cfg = yaml.load(f)

