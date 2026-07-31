# 04 — Project: Cloud Operations Lab

## Overview

**Cloud Operations Lab** is a portfolio project by Martín Lavín (Martin Lavin) that demonstrates end-to-end Cloud Engineering skills: Infrastructure as Code, secure remote access, observability, operational automation, and CI/CD with approval gates.

Repository: github.com/mlavinc/cloud-operations-lab

## What it demonstrates

| Skill area | Implementation |
|---|---|
| Infrastructure as Code | Modular Terraform with remote state (S3 + DynamoDB locking) |
| Networking | VPC, public subnet, Internet Gateway, route tables, security groups |
| Compute | EC2 on Amazon Linux 2023 with IMDSv2 |
| Secure access | SSM Session Manager (no SSH, no open ports, no key pairs) |
| IAM | Least-privilege roles, instance profiles, scoped policies |
| Observability | CloudWatch Agent, logs, CPU alarm, SNS email alerts |
| Ops automation | SSM Run Command documents, Bash scripts, DynamoDB ops event log |
| CI/CD | GitHub Actions with OIDC (no long-lived AWS keys) |
| Deployment control | GitHub Environments + manual approval before terraform apply |

## Technology stack

AWS (EC2, IAM, VPC, CloudWatch, SSM, S3, DynamoDB, SNS), Terraform, Bash, Python, GitHub Actions, OIDC.

## Natural-language Q&A

**Tell me about the Cloud Operations Lab / Explain Cloud Operations Lab.**
It is Martín's AWS operations lab built entirely with Terraform. It focuses on IaC, networking, IAM, EC2, Systems Manager, CloudWatch, GitHub Actions OIDC CI/CD, and operational automation rather than only provisioning resources.

**What cloud skills does Martin demonstrate here?**
IaC with Terraform, secure SSM access, least-privilege IAM, CloudWatch observability, operational automation, and production-like CI/CD with manual approval gates.
