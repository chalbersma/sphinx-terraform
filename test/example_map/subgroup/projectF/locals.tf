# Project Locals
locals {
  full_bucket_name = "${var.environment}-${var.bucket_name}"

  common_tags = merge(
    {
      Environment = var.environment
      Owner       = var.owner
      ManagedBy   = "terraform"
    },
    var.tags
  )
}
