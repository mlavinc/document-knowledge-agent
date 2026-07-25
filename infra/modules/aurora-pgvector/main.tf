# Aurora PostgreSQL Serverless v2 + pgvector, accedido exclusivamente
# vía RDS Data API. Esto permite que las Lambdas NO necesiten estar
# dentro de una VPC (ni NAT Gateway ni ENIs), ya que Data API es HTTPS
# hacia el plano de control de RDS.
#
# El cluster igual debe vivir en subnets de una VPC (requisito de RDS),
# pero se reutiliza la VPC/subnets por defecto de la cuenta para evitar
# crear una VPC dedicada: no aporta valor en este proyecto y no hay
# tráfico de red directo que proteger (nada se conecta por TCP salvo el
# plano de control de AWS).
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.cluster_identifier}-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_security_group" "this" {
  name        = "${var.cluster_identifier}-sg"
  description = "Aurora ${var.cluster_identifier}. No ingress rules: access is via the RDS Data API, not direct TCP connections."
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_rds_cluster" "this" {
  cluster_identifier     = var.cluster_identifier
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = var.engine_version
  database_name          = var.database_name
  master_username        = "ragagent_admin"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]

  enable_http_endpoint = true

  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }

  storage_encrypted      = true
  skip_final_snapshot    = true
  apply_immediately      = true
}

resource "aws_rds_cluster_instance" "this" {
  cluster_identifier = aws_rds_cluster.this.id
  instance_class      = "db.serverless"
  engine              = aws_rds_cluster.this.engine
  engine_version      = aws_rds_cluster.this.engine_version
}
