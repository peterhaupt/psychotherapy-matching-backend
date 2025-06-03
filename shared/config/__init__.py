"""Shared configuration package for the therapy platform."""
from .settings import config, get_config, Config, DevelopmentConfig, ProductionConfig, TestConfig

__all__ = [
    'config',
    'get_config',
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestConfig'
]