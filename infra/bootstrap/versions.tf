terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Este stage se aplica con estado LOCAL, a propósito: es el único punto
  # de la infraestructura que no puede depender de un backend remoto,
  # porque su trabajo es precisamente crear ese backend.
}
