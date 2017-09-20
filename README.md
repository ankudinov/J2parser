# Jinja2 Parser (j2p)

NOTE: recently discovered [jinja2schema](http://jinja2schema.aromanovich.ru/) library. Looks very promising, updates coming soon.

Jinja2 parser is a simple tool for network engineers that can be used:
- to walk over Jinja2 Abstract Syntax Tree to extract variables, that can not be extracted by Jinja2.meta.
- to save extracted variables in YAML format.
- as a lightweight config generator.  

Extracting variables helps to save time when building Ansible playbooks, etc.  
Some reasonably complicated templates with `for`, `if` and `include` attached to illustrate the process.  

Example:  
```text
./j2p.py vlan.j2 j2 > variables.yaml
cat ./variables.yaml

vlan_list:
- name: '{{ not defined }}'
  number: '{{ not defined }}'
  vni: '{{ not defined }}'
- '{{ more elements in the list }}'
vxlan:
  loopback:
    description: '{{ not defined }}'
    ip: '{{ not defined }}'
    mask: '{{ not defined }}'
    number: '{{ not defined }}'
  required: '{{ not defined }}'
  vtep_list:
  - '{{ not defined }}'
  - '{{ more elements in the list }}'
```

Extracting variables is based on J2 AST recursive walk. The process is rather empiric and therefore has some limitations.
Filters and other advanced features are not supported, but usually not required to build typical network automation template.  
Additional testing is required to find out possible corner cases. If you hit the bug, please share your feedback and the template.
Any ideas on how to make the process more generic are welcome.

To use the tool as config generator, following files are required:
- `settings.yaml` - used to specify templates, tasks, configs directories and YAML database
- `db.yaml` - database of network elements in YAML format
- config generator task in YAML format.

Database is a simple dictionary with the hostname or management IP as ID and a list of tags:
```yaml
id: [tag1, tag2, tag3]
```

After extracting variables, we can use YAML to build the task.
Take a look at `test-task.yaml` example.
Variables should always be specified first with corresponding tags.
Same tags should be used for the list of templates to render.

Execute following command:
```text
./j2p.py test-task.yaml yaml save
```

That will build configs with timestamps in `generated_configs` directory.
Configs with same VLANs, but different loopbacks and flood lists will be generated for 3 MLAG clusters.

Use `./j2p.py test-task.yaml yaml save -p prefix` to specify the name prefix for produced configs.

Required:
- Jinja2 (2.9.6)
- PyYAML