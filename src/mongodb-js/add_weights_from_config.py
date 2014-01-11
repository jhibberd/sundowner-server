"""Dynamically add score weights from the YAML config file to the MongoDB
script file.

This allows all system components to be configured from a single config file.

Usage:
    
    cat update-score.js | python add_weights_from_config.py /home/jhibberd/projects/sundowner/cfg/dev.yaml | mongo

"""

import sys
import yaml


# load config
config_path = sys.argv[1]
with open(config_path) as f:
    cfg = yaml.load(f)

# write config to head of script file
weights = cfg["score-weights"]
for line in [
        "var cfgWeightVote = %s;" %             weights["vote"],
        "var cfgWeightDayOffset = %s;" %        weights["day_offset"],
        "var cfgWeightWeekOffset = %s;" %       weights["week_offset"],
        "var cfgDbNamePrimary = '%s';" %        cfg["db-name-primary"],   
        ]:
    sys.stdout.write(line + "\n")

# write script file
for line in sys.stdin.readlines():
    sys.stdout.write(line)

