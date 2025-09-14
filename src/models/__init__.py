"""
Data models for Bakin documentation scraper.

This package contains all the data classes used to represent
documentation elements extracted from the Bakin C# reference.
"""

from .basic_models import (
    ParameterInfo,
    ExceptionInfo,
    ConstructorInfo,
    MethodInfo,
    PropertyInfo,
    FieldInfo,
    EventInfo
)

from .main_models import (
    ClassInfo,
    NamespaceInfo
)

__all__ = [
    'ParameterInfo',
    'ExceptionInfo',
    'ConstructorInfo',
    'MethodInfo',
    'PropertyInfo',
    'FieldInfo',
    'EventInfo',
    'ClassInfo',
    'NamespaceInfo'
]