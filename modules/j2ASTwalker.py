#!/usr/bin/env python3

__author__ = 'Petr Ankudinov'

from jinja2 import meta, FileSystemLoader
import jinja2.nodes
import os
import sys
import yaml
from modules.tools import merge_dict, build_dict


def build_dict_recursive(lst_or_tpl):
    # Recursive function that builds a hierarchical dictionary from lists and sublists of (key_list, value) tuples.

    if isinstance(lst_or_tpl, tuple):
        if isinstance(lst_or_tpl[1], list):
            value = list()
            for e in lst_or_tpl[1]:
                value.append(build_dict_recursive(e))
        elif isinstance(lst_or_tpl[1], tuple):
            value = build_dict_recursive(lst_or_tpl[1])
        else:
            value = lst_or_tpl[1]
        result = build_dict(list(reversed(lst_or_tpl[0])), value)
    elif isinstance(lst_or_tpl, list):
        result = dict()
        for e in lst_or_tpl:
            result = merge_dict(result, build_dict_recursive(e))
    else:
        result = lst_or_tpl

    return result


value_dict = {
    # these values will be assigned to extracted variables
    'not defined': '{{ not defined }}',
    'error': 'Error!',
    'list': '{{ more elements in the list }}',
}


class J2Meta:

    def __init__(self, template_realpath):
        self.env = jinja2.Environment(loader=FileSystemLoader(searchpath=os.path.dirname(template_realpath)))
        self.parent_template = os.path.basename(template_realpath)
        self.known_templates = self.get_known_templates(self.parent_template)

    # INTERNAL methods

    def get_known_templates(self, template_name):
        # initialise known template list and append parent template name
        known_template_list = set()
        known_template_list.add(template_name)
        # parse parent template
        template_src = self.env.loader.get_source(self.env, template_name)[0]
        parsed_template = self.env.parse(source=template_src)
        # get referenced templates and walk over these templates recursively
        referenced_template_list = meta.find_referenced_templates(parsed_template)
        for child_template in referenced_template_list:
            known_template_list.add(child_template)
            known_template_list.update(self.get_known_templates(child_template))
        # return parent and all child template names
        return known_template_list

    def j2_ast_walk_main(self, j2node):
        # The script will start walking over Jinja2 AST here looking for Getattr, Assign, Name, For nodes.
        result_list = list()
        recursion_required_nodes = [jinja2.nodes.Template, jinja2.nodes.Output]
        recursion_required = False
        for node in recursion_required_nodes:
            if isinstance(j2node, node):
                recursion_required = True
        if recursion_required:
            for child_node in j2node.iter_child_nodes():
                # Recursion to get more specific nodes
                for e in self.j2_ast_walk_main(child_node):
                    result_list.append(e)
        else:
            # Node specific walk
            if isinstance(j2node, jinja2.nodes.For):
                for e in self.j2_ast_walk_for(j2node):
                    result_list.append(e)
            if isinstance(j2node, jinja2.nodes.If):
                for e in self.j2_ast_walk_if(j2node):
                    result_list.append(e)
            if isinstance(j2node, jinja2.nodes.Getattr):
                for e in self.j2_ast_walk_getattr(j2node):
                    result_list.append(e)
            if isinstance(j2node, jinja2.nodes.Assign):
                for e in self.j2_ast_walk_assign(j2node):
                    result_list.append(e)
            if isinstance(j2node, jinja2.nodes.Name):
                for e in self.j2_ast_walk_name(j2node):
                    result_list.append(e)
            # Ignore following nodes
            ignored_node_list = [
                jinja2.nodes.TemplateData,
                jinja2.nodes.Literal,
                jinja2.nodes.Expr,
                jinja2.nodes.Const,
                jinja2.nodes.Include,
            ]
            for ignored_node in ignored_node_list:
                if isinstance(j2node, ignored_node):
                    pass  # do nothing
            # Generate alert for future debugging
            alert_nodes_list = [
                jinja2.nodes.Macro,
                jinja2.nodes.CallBlock,
                jinja2.nodes.FilterBlock,
                jinja2.nodes.With,
                jinja2.nodes.Block,
                jinja2.nodes.Import,
                jinja2.nodes.FromImport,
                jinja2.nodes.ExprStmt,
                jinja2.nodes.AssignBlock,
                jinja2.nodes.BinExpr,
                jinja2.nodes.UnaryExpr,
                jinja2.nodes.NSRef,
                jinja2.nodes.Tuple,
                jinja2.nodes.List,
                jinja2.nodes.Dict,
                jinja2.nodes.Pair,
                jinja2.nodes.Keyword,
                jinja2.nodes.CondExpr,
                jinja2.nodes.Filter,
                jinja2.nodes.Test,
                jinja2.nodes.Call,
                jinja2.nodes.Getitem,
                jinja2.nodes.Slice,
                jinja2.nodes.Concat,
                jinja2.nodes.Compare,
                jinja2.nodes.Operand,
            ]
            for i, ignored_node in enumerate(alert_nodes_list):
                if isinstance(j2node, ignored_node):
                    print("Ignoring %s!" % alert_nodes_list[i], file=sys.stderr)
                    print(j2node, file=sys.stderr)

        return result_list

    @staticmethod
    def j2_ast_walk_name(j2node):
        key_list = [j2node.name]
        value = False
        if j2node.ctx == 'load':
            value = value_dict['not defined']
        else:  # ctx == 'store'
            pass  # ctx should be 'load' for Name node
        if not value:
            value = value_dict['error']
        key_list = list(key_list)
        return [(key_list, value)]  # return a list with a single tuple

    def j2_ast_walk_getattr(self, j2node):
        result_list = list()
        for child_node in j2node.iter_child_nodes():
            for e in self.j2_ast_walk_main(child_node):
                result_list.append(e)
        for tpl in result_list:
            tpl[0].append(j2node.attr)  # add parent key to each tuple
        return result_list

    def j2_ast_walk_assign(self, j2node):
        key_list = list()
        value = False
        for child in j2node.iter_child_nodes():
            if isinstance(child, jinja2.nodes.Name):
                if child.ctx == 'store':  # 'store' should be the only context for Assign node
                    key_list.append(child.name)
                else:
                    value = child.name
            if isinstance(child, jinja2.nodes.Pair):
                if isinstance(child.value, jinja2.nodes.Const):
                    if not value:
                        value = child.value.value
                if isinstance(child.value, jinja2.nodes.Name):
                    if not value:
                        value = child.value.name
                if isinstance(child.value, jinja2.nodes.Dict):
                    for temp_list, value in self.j2_ast_walk_assign(child.value):
                        key_list = key_list + temp_list
                key_list.append(child.key.value)
            if isinstance(child, jinja2.nodes.Dict):
                temp_list, value = self.j2_ast_walk_assign(child)
                key_list = key_list + temp_list
        key_list = list(reversed(key_list))
        return [(key_list, value)]

    def j2_ast_walk_for(self, j2node):
        result_list = list()
        iter_list = self.j2_ast_walk_main(j2node.iter)

        target_key_list = self.j2_ast_walk_main(j2node.target)  # value will be ignored
        target_key_length = len(target_key_list)

        target_child_key_list = list()
        for node in j2node.body:
            for e in self.j2_ast_walk_main(node):
                for tk in target_key_list:
                    if e[0][:target_key_length] == tk[0]:
                        if e[0][target_key_length:]:  # verify if there are any other key apart from target
                            target_child_key_list.append((e[0][target_key_length:], e[1]))
                    else:
                        result_list.append(e)
        for ik in iter_list:
            if target_child_key_list:
                result_list.append((ik[0], [target_child_key_list, value_dict['list']]))
            else:
                result_list.append((ik[0], [ik[1], value_dict['list']]))

        return result_list

    def j2_ast_walk_if(self, j2node):
        result_list = list()

        if isinstance(j2node.test, jinja2.nodes.Compare):
            for key_list, value in self.j2_ast_walk_getattr(j2node.test.expr):
                result_list.append((key_list, value))

        for node in j2node.body:
            for key_list, value in self.j2_ast_walk_main(node):
                result_list.append((key_list, value))

        for node in j2node.else_:
            for key_list, value in self.j2_ast_walk_main(node):
                result_list.append((key_list, value))

        return result_list

    # EXTERNAL methods

    def get_template_list(self):
        return self.known_templates

    def parse(self, variables):
        j2_template = self.env.get_template(self.parent_template)  # get parent template
        config = j2_template.render(variables)
        return config

    def get_variables(self):
        result_list = list()
        for template in self.known_templates:
            template_src = self.env.loader.get_source(self.env, template)[0]
            parsed_template = self.env.parse(source=template_src)
            for e in self.j2_ast_walk_main(parsed_template):
                result_list.append(e)

        var_dict = build_dict_recursive(result_list)

        return var_dict


if __name__ == '__main__':
    # Extract variables from the specified template and display as YAML
    template_name = sys.argv[1]
    template_meta = J2Meta(template_name)
    print(
        yaml.dump(template_meta.get_variables(), default_flow_style=False)
    )
