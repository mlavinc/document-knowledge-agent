"""Resolve secrets from the environment or AWS SSM Parameter Store."""

from __future__ import annotations

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

_cached_openai_api_key: str | None = None


def resolve_openai_api_key(
    *,
    api_key: str,
    ssm_parameter_name: str,
    aws_region: str,
) -> str:
    """
    Prefer an explicit OPENAI_API_KEY (local/dev). In production the Lambda
    receives only OPENAI_API_KEY_SSM_PARAMETER (parameter name); the value
    is fetched at runtime from SSM SecureString so it never lives in
    Terraform state or Lambda env plaintext.
    """
    global _cached_openai_api_key

    if api_key:
        return api_key

    if _cached_openai_api_key is not None:
        return _cached_openai_api_key

    if not ssm_parameter_name:
        return ""

    try:
        client = boto3.client("ssm", region_name=aws_region)
        response = client.get_parameter(
            Name=ssm_parameter_name,
            WithDecryption=True,
        )
        value = response["Parameter"]["Value"]
    except (BotoCoreError, ClientError, KeyError) as error:
        logger.error(
            "Failed to load OpenAI API key from SSM parameter %s: %s",
            ssm_parameter_name,
            error,
        )
        raise RuntimeError(
            f"Unable to resolve OpenAI API key from SSM parameter "
            f"'{ssm_parameter_name}'"
        ) from error

    _cached_openai_api_key = value
    return value
