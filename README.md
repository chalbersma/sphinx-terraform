# sphinx-terraform-ch

A Sphinx extension that auto-generates documentation for Terraform modules directly from HCL source files. 

**Based on the original [sphinx-terraform](https://github.com/cblegare/sphinx-terraform) by Charles Bouchard-Légaré.** 

This fork (`sphinx-terraform-ch`) rewrites the extension with a new Sphinx domain, block renderer, and module parser.

## Features

- `tfmodule` directive: auto-document one or more Terraform modules from a path
- `tf:` Sphinx domain: manually document individual Terraform objects with cross-reference support
- `tfreport` CLI: generate Markdown documentation from the command line
- Supports all standard Terraform block types: `resource`, `variable`, `locals`, `data`, `terraform`, `module`, 
  0.
- `provider`, `check`, `import`, `removed`
- Extracts preceding HCL comments (`#`, `//`, `/* */`) as block descriptions
- Cross-module cross-referencing via `tf:project` namespaces

## Installation

```bash
pip install sphinx-terraform-ch
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add sphinx-terraform-ch
```

## Configuration

Add the extension and MyST parser to your `conf.py`:

```python
extensions = [
    "sphinx_terraform_ch",
    "myst_parser",
]
```

## Usage

### `tfmodule` Directive

The `tfmodule` directive scans a directory for `.tf` files and renders documentation for every block found.

```rst
.. tfmodule::
   :path: ../terraform/modules
   :submodules_depth: 1
   :ignore: ["\.terraform", "examples"]
   :hide_nocomment:
```

**Options:**

| Option | Description |
|---|---|
| `:path:` | Path to the Terraform module directory (required) |
| `:submodules_depth:` | How many directory levels deep to look for submodules (default: `0`, meaning the path itself) |
| `:ignore:` | JSON array of regex patterns — subdirectories whose names match are skipped |
| `:hide_nocomment:` | Flag. If set, blocks without a preceding comment are omitted from output |

**Example — document a single module:**

```rst
.. tfmodule::
   :path: ./terraform
```

**Example — document all submodules one level deep, skipping test directories:**

```rst
.. tfmodule::
   :path: ./terraform/modules
   :submodules_depth: 1
   :ignore: ["test", "examples"]
```

**Example — only show documented blocks:**

```rst
.. tfmodule::
   :path: ./terraform
   :hide_nocomment:
```

---

### `tf:` Domain Directives

You can manually document Terraform objects using the `tf:` domain. These support cross-referencing across your Sphinx project.

**Supported directives:**

```rst
.. tf:resource:: aws_instance web

.. tf:variable:: region

.. tf:locals::

.. tf:data:: aws_ami ubuntu

.. tf:module:: vpc

.. tf:provider:: aws

.. tf:terraform::

.. tf:check:: health

.. tf:import::

.. tf:removed::
```

**Cross-reference roles:**

| Role | Object Type |
|---|---|
| `:tf:res:` | resource |
| `:tf:var:` | variable |
| `:tf:local:` | locals |
| `:tf:data:` | data |
| `:tf:mod:` | module |
| `:tf:prov:` | provider |
| `:tf:tf:` | terraform |
| `:tf:check:` | check |

Example cross-reference:

```rst
See :tf:var:`region` and :tf:res:`aws_instance.web`.
```

---

### `tf:project` Namespace

When documenting multiple modules, use `tf:project` to scope cross-references so that names do not collide across modules.

```rst
.. tf:project:: projectA

.. tf:variable:: region

See :tf:var:`region` (resolves within projectA).

.. tf:project:: None
```

The `tfmodule` directive sets this automatically for each module it renders.

---

### `tfreport` CLI

`tfreport` generates Markdown documentation for a Terraform module from the command line.

```
usage: tfreport [-h] [--level LEVEL] [-v] path

Generate a Terraform documentation report for a module path.

positional arguments:
  path           Path to the Terraform module directory.

options:
  --level LEVEL  Heading level for the generated report (default: 1).
  -v, --verbose  Verbosity controls (repeat for more output: -v, -vv, -vvv).
```

**Example:**

```bash
tfreport ./terraform/modules/vpc
tfreport ./terraform/modules/vpc --level 2 -v
```

Output is Markdown printed to stdout, suitable for piping or redirecting into a file.

---

## HCL Comment Support

Comments placed immediately before a block (no blank lines between) are extracted and used as the block description. All HCL comment styles are supported:

```hcl
# This is a variable for the AWS region.
variable "region" {
  type    = string
  default = "us-east-1"
}

// Multi-word resource description.
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t3.micro"
}

/*
 * This locals block computes derived values.
 */
locals {
  name_prefix = "myapp-${var.env}"
}
```

---

## License

BSD-2-Clause-Patent. See [LICENSE](LICENSE) for details.

Original work copyright (c) 2022 Charles Bouchard-Légaré.
