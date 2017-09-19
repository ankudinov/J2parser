#!/usr/bin/env python3

__author__ = 'Petr Ankudinov'

from modules.j2ASTwalker import J2Meta
from modules import tools, delivery
import sys
import yaml
import os
import argparse


class ArgParser:

    def __init__(self, args=False):  # arguments should be passed by unit test only
        parser = argparse.ArgumentParser(description='\
        Jinja2 Parser: YAML-builder and lightweight config generator.', epilog='Thank you for using help!')
        parser.add_argument('filename', help='Filename.')
        parser.add_argument('file_type', help='Jinja2 or YAML file.',
                            choices=['j2', 'yaml'])

        subparsers = parser.add_subparsers(help='Select delivery mode, YAML only.', dest='mode')
        save_parser = subparsers.add_parser('save', help='Save generated configs in a directory specified in settings.')
        save_parser.add_argument('-p', '--prefix', help='Config filename prefix.', dest='prefix', default=False)

        if args:  # if arguments are passed from unittest
            self.args = parser.parse_args(args)
        else:
            self.args = parser.parse_args()

    def prefix(self):
        if self.args.mode == 'save':
            return self.args.prefix
        else:
            return False

    def mode(self):
        return self.args.mode

    def file_type(self):
        return self.args.file_type

    def filename(self):
        return self.args.filename


class ScriptEnvironment:

    def __init__(self, cli_args, settings_file='./settings.yaml'):
        self.script_realpath = os.path.realpath(__file__)
        self.script_dirname = os.path.dirname(self.script_realpath)
        try:
            # load parameters from settings file
            settings = tools.load_yaml(os.path.realpath(settings_file))
            self.template_path = self.get_dir(settings['template_path'])
            self.configs_path = self.get_dir(settings['configs'])
            self.task_path = self.get_dir(settings['task_path'])
            db_name = self.get_file(self.script_realpath, settings['host_db'])
            self.json_db = tools.load_yaml(db_name)
            if not isinstance(self.json_db, dict):
                sys.exit('ERROR: Wrong db format. Database file should be a dictionary!')
            # get parameters from CLI
            self.file_type = cli_args.file_type()
            if self.file_type == "yaml":
                self.filename = self.get_file(self.task_path, cli_args.filename())
                self.json_data = tools.load_yaml(self.filename)
                self.mode = cli_args.mode()
                if self.mode == 'save':
                    self.prefix = cli_args.prefix()
            else:
                self.filename = self.get_file(self.template_path, cli_args.filename())
        except Exception as _:
            sys.exit('ERROR: Can not load settings!')

    def get_dir(self, dir_name):
        if os.path.isdir(dir_name):
            return dir_name
        else:
            template_dir = os.path.join(self.script_realpath, dir_name)
            if os.path.isdir(template_dir):
                return template_dir
            else:
                sys.exit('ERROR: Can not find directory %s!' % dir_name)

    def get_file(self, dir, file_name):
        if os.path.isfile(file_name):
            return file_name
        else:
            file = os.path.join(dir, file_name)
            if os.path.isfile(file):
                return file
            else:
                sys.exit('ERROR: Can not find file %s!' % file_name)


if __name__ == '__main__':
    # define script environment
    cli_args = ArgParser()
    env = ScriptEnvironment(cli_args)

    # delivery.run(env)

    if env.file_type == 'j2':
        template_meta = J2Meta(env.filename)
        print(
            yaml.dump(template_meta.get_variables(), default_flow_style=False)
        )

    if env.file_type == 'yaml':
        if env.mode == 'save':
            delivery.save_configs(env)
