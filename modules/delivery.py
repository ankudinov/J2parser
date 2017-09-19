__author__ = 'Petr Ankudinov'

from modules import tools
import os
import sys
import jinja2


def build_configs(env):
    db = env.json_db
    json_data = env.json_data
    variables = dict()
    configs = dict()
    for block in json_data:
        if 'variables' in block.keys():
            tags = set(block['tags'])
            for host in db.keys():
                db_tags = set(db[host])
                if tags.issubset(db_tags):
                    try:
                        variables[host]
                    except:
                        variables[host] = block['variables']
                    else:
                        variables[host] = tools.merge_dict(variables[host], block['variables'])

        if 'templates' in block.keys():
            tags = set(block['tags'])
            for host in db.keys():
                db_tags = set(db[host])
                if tags.issubset(db_tags):

                    try:
                        configs[host]
                    except:
                        configs[host] = dict()
                        configs[host]['configuration'] = ''
                        configs[host]['mode'] = False
                        configs[host]['login'] = False
                        configs[host]['password'] = False

                    for j2 in block['templates']:
                        if os.path.isfile(j2):
                            template_search_path = os.path.dirname(j2)
                            template_filename = os.path.basename(j2)
                        else:
                            filename = os.path.join(env.template_path, j2)
                            template_search_path = os.path.dirname(filename)
                            template_filename = os.path.basename(filename)

                        j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=template_search_path))
                        j2_template = j2_env.get_template(template_filename)

                        try:
                            config = j2_template.render(variables[host])
                            configs[host]['configuration'] = configs[host]['configuration'] + '\n' + config

                        except Exception as _:
                            try:
                                config = j2_template.render()
                                configs[host]['configuration'] = configs[host]['configuration'] + '\n' + config
                            except Exception as _:
                                sys.exit('ERROR: Not able to parse template ' + template_filename + '!')
    return configs


def save_configs(env):
    configs = build_configs(env)
    for ip in configs.keys():
        filename = ''
        if env.prefix:
            filename += env.prefix + '_'
        filename += ip + '_' + str(tools.time_stamp()) + '.txt'
        realpath = os.path.join(env.configs_path, filename)
        try:
            file = open(realpath, mode='w')
        except Exception as _:
            print('ERROR: Can not create ', realpath)
            sys.exit('ERROR: Can not create ' + realpath)
        else:
            file.write(configs[ip]['configuration'])
            file.close()


def ssh():
    pass


def eapi():
    pass
