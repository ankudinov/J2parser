#!/usr/bin/env python3

from modules.j2ASTwalker import J2Meta
import sys
import yaml


if __name__ == '__main__':
    # Extract variables from the specified template and display as YAML
    template_name = sys.argv[1]
    template_meta = J2Meta(template_name)
    print(
        yaml.dump(template_meta.get_variables(), default_flow_style=False)
    )
