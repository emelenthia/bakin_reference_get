"""
Basic data models for Bakin documentation scraper.

This module contains the fundamental data classes used to represent
documentation elements extracted from the Bakin C# reference.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParameterInfo:
    """Represents a method or constructor parameter."""
    name: str
    type: str
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ParameterInfo':
        """Create instance from dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            description=data.get('description')
        )


@dataclass
class ExceptionInfo:
    """Represents an exception that can be thrown by a method."""
    type: str
    description: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExceptionInfo':
        """Create instance from dictionary."""
        return cls(
            type=data['type'],
            description=data['description']
        )


@dataclass
class ConstructorInfo:
    """Represents a class constructor."""
    name: str
    parameters: List[ParameterInfo]
    description: Optional[str] = None
    access_modifier: str = "public"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'parameters': [param.to_dict() for param in self.parameters],
            'description': self.description,
            'accessModifier': self.access_modifier
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConstructorInfo':
        """Create instance from dictionary."""
        parameters = [ParameterInfo.from_dict(param) for param in data.get('parameters', [])]
        return cls(
            name=data['name'],
            parameters=parameters,
            description=data.get('description'),
            access_modifier=data.get('accessModifier', 'public')
        )


@dataclass
class MethodInfo:
    """Represents a class method."""
    name: str
    return_type: str
    parameters: List[ParameterInfo]
    description: Optional[str] = None
    is_static: bool = False
    access_modifier: str = "public"
    exceptions: Optional[List[ExceptionInfo]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'returnType': self.return_type,
            'parameters': [param.to_dict() for param in self.parameters],
            'description': self.description,
            'isStatic': self.is_static,
            'accessModifier': self.access_modifier,
            'exceptions': [exc.to_dict() for exc in self.exceptions] if self.exceptions else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MethodInfo':
        """Create instance from dictionary."""
        parameters = [ParameterInfo.from_dict(param) for param in data.get('parameters', [])]
        exceptions = None
        if data.get('exceptions'):
            exceptions = [ExceptionInfo.from_dict(exc) for exc in data['exceptions']]
        
        return cls(
            name=data['name'],
            return_type=data['returnType'],
            parameters=parameters,
            description=data.get('description'),
            is_static=data.get('isStatic', False),
            access_modifier=data.get('accessModifier', 'public'),
            exceptions=exceptions
        )


@dataclass
class PropertyInfo:
    """Represents a class property."""
    name: str
    type: str
    description: Optional[str] = None
    access_modifier: str = "public"
    getter: bool = True
    setter: bool = True
    is_static: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'accessModifier': self.access_modifier,
            'getter': self.getter,
            'setter': self.setter,
            'isStatic': self.is_static
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PropertyInfo':
        """Create instance from dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            description=data.get('description'),
            access_modifier=data.get('accessModifier', 'public'),
            getter=data.get('getter', True),
            setter=data.get('setter', True),
            is_static=data.get('isStatic', False)
        )


@dataclass
class FieldInfo:
    """Represents a class field."""
    name: str
    type: str
    description: Optional[str] = None
    access_modifier: str = "public"
    is_static: bool = False
    is_readonly: bool = False
    value: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'accessModifier': self.access_modifier,
            'isStatic': self.is_static,
            'isReadonly': self.is_readonly,
            'value': self.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FieldInfo':
        """Create instance from dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            description=data.get('description'),
            access_modifier=data.get('accessModifier', 'public'),
            is_static=data.get('isStatic', False),
            is_readonly=data.get('isReadonly', False),
            value=data.get('value')
        )


@dataclass
class EventInfo:
    """Represents a class event."""
    name: str
    type: str
    description: Optional[str] = None
    access_modifier: str = "public"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'accessModifier': self.access_modifier
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EventInfo':
        """Create instance from dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            description=data.get('description'),
            access_modifier=data.get('accessModifier', 'public')
        )