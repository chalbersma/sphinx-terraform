// Documentation for terraform/main.tf
//
// * list item 1
// * list item 2
//
// Even inline **formatting** in *here* is possible.
// and some link  [inline link ](https://example.com/),
// [internal_link](#tf.variable.submodule-input)
//
terraform {
  required_version = ">= 0.12"
  required_providers {
    foo = {
      source  = "https://registry.acme.com/foo"
      version = ">= 1.0"
    }
  }
}

module "foobar" {
  source = "git@github.com:module/path?ref=v7.8.9"
}

module "sub" {

}

/**
  Here is a ``resource``.

  .. code-block:: shell

      rm -rf /somepath

  look out :tf:data:`foo_data.qux`
 */
resource "foo_resource" "baz" {
}

/**
  Here is documentation in Markdown (MyST).

  Use it like so:

  Also, an [hyperlink](https://cblegare.gitlab.io/sphinx-terraform).

 */
resource "foo_resource" "markdown" {
}

# Documentation for this data.
#
# Might be somewhat related to :tf:resource:`foo_resource.baz`.
data "foo_data" "qux" {
}
