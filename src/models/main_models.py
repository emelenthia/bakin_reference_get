"""
Main data models for Bakin documentation scraper.

This module contains the primary data classes used to represent
namespaces and classes extracted from the Bakin C# reference.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .basic_models import (
    ConstructorInfo, MethodInfo, PropertyInfo, 
    FieldInfo, EventInfo
)


@dataclass
class ClassInfo:
    """Represents a C# class with all its members."""
    name: str
    full_name: str
    url: str
    description: Optional[str] = None
    inheritance: Optional[str] = None
    constructors: List[ConstructorInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    properties: List[PropertyInfo] = field(default_factory=list)
    fields: List[FieldInfo] = field(default_factory=list)
    events: List[EventInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'fullName': self.full_name,
            'url': self.url,
            'description': self.description,
            'inheritance': self.inheritance,
            'constructors': [constructor.to_dict() for constructor in self.constructors],
            'methods': [method.to_dict() for method in self.methods],
            'properties': [prop.to_dict() for prop in self.properties],
            'fields': [field.to_dict() for field in self.fields],
            'events': [event.to_dict() for event in self.events]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ClassInfo':
        """Create instance from dictionary."""
        constructors = [ConstructorInfo.from_dict(c) for c in data.get('constructors', [])]
        methods = [MethodInfo.from_dict(m) for m in data.get('methods', [])]
        properties = [PropertyInfo.from_dict(p) for p in data.get('properties', [])]
        fields = [FieldInfo.from_dict(f) for f in data.get('fields', [])]
        events = [EventInfo.from_dict(e) for e in data.get('events', [])]
        
        return cls(
            name=data['name'],
            full_name=data['fullName'],
            url=data['url'],
            description=data.get('description'),
            inheritance=data.get('inheritance'),
            constructors=constructors,
            methods=methods,
            properties=properties,
            fields=fields,
            events=events
        )


@dataclass
class NamespaceInfo:
    """Represents a C# namespace containing classes."""
    name: str
    url: str
    classes: List[ClassInfo] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'classes': [cls.to_dict() for cls in self.classes]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NamespaceInfo':
        """Create instance from dictionary."""
        classes = [ClassInfo.from_dict(c) for c in data.get('classes', [])]
        
        return cls(
            name=data['name'],
            url=data['url'],
            classes=classes,
            description=data.get('description')
        )