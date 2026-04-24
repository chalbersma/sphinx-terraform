#!/usr/bin/env python3


from typing import Dict, List, Tuple
from docutils import nodes
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import TypedField, GroupedField, Field


class TerraformObject(ObjectDescription):
    """
    Generic directive for all Terraform blocks.
    Handles:
    - Type + Name: .. tf:resource:: aws_instance web
    - Name only:   .. tf:variable:: region
    - No name:     .. tf:locals::
    """

    doc_field_types = [
        # For Variables/Resources: type and description
        TypedField('parameter', label='Arguments',
                   names=('arg', 'param', 'input'),
                   typerolename='obj', typenames=('type',)),

        # For Outputs/Attributes
        GroupedField('attribute', label='Attributes',
                     names=('attr', 'output', 'export')),

        # For generic metadata (like "Default" or "Required")
        Field('default', label='Default Value', has_arg=False, names=('default',)),
        Field('required', label='Required', has_arg=False, names=('required',)),
    ]

    def handle_signature(self, sig: str, signode: addnodes.desc_signature) -> str:
        # Clean quotes if user used HCL style: resource "aws_instance" "web"
        parts = [p.strip('"') for p in sig.split()]
        obj_type = self.objtype

        if len(parts) >= 2:
            # Case: resource "aws_instance" "web"
            resource_type, resource_name = parts[0], parts[1]
            signode += addnodes.desc_annotation(f"{obj_type} ", f"{obj_type} ")
            signode += addnodes.desc_type(resource_type + " ", resource_type + " ")
            signode += addnodes.desc_name(resource_name, resource_name)
            return f"{resource_type}.{resource_name}"

        elif len(parts) == 1:
            # Case: variable "region"
            name = parts[0]
            signode += addnodes.desc_annotation(f"{obj_type} ", f"{obj_type} ")
            signode += addnodes.desc_name(name, name)
            return name

        else:
            # Case: locals or terraform (no arguments)
            label = obj_type.capitalize()
            signode += addnodes.desc_name(label, label)
            return obj_type

    def add_target_and_index(self, name: str, sig: str, signode: addnodes.desc_signature):
        # Create a unique internal ID to prevent collisions between a var and resource of same name
        target_id = f"tf.{self.objtype}.{name}"

        if target_id not in self.state.document.ids:
            signode['names'].append(target_id)
            signode['ids'].append(target_id)
            self.state.document.note_explicit_target(signode)

        # Store in domain data for cross-referencing
        domain = self.env.get_domain('tf')
        domain.add_object(self.objtype, name, target_id)

        # Add to the general index
        self.indexnode['entries'].append(
            ('single', f'{name} (Terraform {self.objtype})', target_id, '', None)
        )


class TerraformDomain(Domain):
    """A Terraform language domain for Sphinx."""
    name = 'tf'
    label = 'Terraform'

    # Mapping of types to their cross-reference roles
    object_types = {
        'resource': ObjType('resource', 'res'),
        'variable': ObjType('variable', 'var'),
        'locals': ObjType('locals', 'local'),
        'data': ObjType('data', 'data'),
        'terraform': ObjType('terraform', 'tf'),
        'module': ObjType('module', 'mod'),
        'provider': ObjType('provider', 'prov'),
        'check': ObjType('check', 'check'),
        'import': ObjType('import', 'import'),
        'removed': ObjType('removed', 'removed'),
        'block': ObjType('block', 'block'),
    }

    directives = {t: TerraformObject for t in object_types}
    roles = {
        'res': XRefRole(),
        'var': XRefRole(),
        'local': XRefRole(),
        'data': XRefRole(),
        'tf': XRefRole(),
        'mod': XRefRole(),
        'prov': XRefRole(),
        'check': XRefRole(),
        'import': XRefRole(),
        'removed': XRefRole(),
        'block': XRefRole(),
    }

    initial_data = {
        'objects': {},  # (objtype, name) -> (docname, target_id)
    }

    def add_object(self, objtype, name, target_id):
        # Stores the object in the environment for persistent builds
        self.data['objects'][objtype, name] = (self.env.docname, target_id)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        # Match the role type (e.g., 'var') back to the object type (e.g., 'variable')
        # This allows :tf:var:`x` to find the 'variable' object
        objtypes = [obj for obj, info in self.object_types.items() if typ in info.roles]

        for objtype in objtypes:
            if (objtype, target) in self.data['objects']:
                docname, target_id = self.data['objects'][objtype, target]
                return make_refnode(builder, fromdocname, docname, target_id, contnode, target)
        return None