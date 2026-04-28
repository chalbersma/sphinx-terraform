/**
 * # Project E - Sample S3 Storage Module
 *
 * This module provisions an S3 bucket for general-purpose object storage.
 *
 * ## Usage
 *
 * ```hcl
 * module "storage" {
 *   source      = "./projectE"
 *   bucket_name = "my-app-data"
 *   environment = "production"
 *   owner       = "platform-team"
 * }
 * ```
 */

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

variable "bucket_name" {
  type        = string
  description = "The base name for the S3 bucket. A suffix will be appended to ensure global uniqueness."
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g. dev, staging, production)."
  default     = "dev"
}

variable "owner" {
  type        = string
  description = "Team or individual responsible for this bucket."
  default     = "unset"
}

variable "versioning_enabled" {
  type        = bool
  description = "Enable S3 object versioning on the bucket."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to all resources."
  default     = {}
}
