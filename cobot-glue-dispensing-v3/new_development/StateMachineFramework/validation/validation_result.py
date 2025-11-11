"""
Validation result classes for state machine validation.

This module provides the ValidationResult dataclass and related utilities
for consistent validation reporting throughout the framework.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
import time


@dataclass
class ValidationError:
    """Represents a single validation error."""
    code: str
    message: str
    field: Optional[str] = None
    value: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.field:
            return f"{self.field}: {self.message} (code: {self.code})"
        return f"{self.message} (code: {self.code})"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    success: bool
    message: str = ""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def success(cls, message: str = "Validation passed") -> 'ValidationResult':
        """
        Create a successful validation result.
        
        Args:
            message: Success message
            
        Returns:
            Successful validation result
        """
        return cls(success=True, message=message)
    
    @classmethod
    def failed(cls, message: str, errors: List[ValidationError] = None) -> 'ValidationResult':
        """
        Create a failed validation result.
        
        Args:
            message: Failure message
            errors: List of validation errors
            
        Returns:
            Failed validation result
        """
        return cls(
            success=False, 
            message=message, 
            errors=errors or []
        )
    
    @classmethod
    def error(cls, code: str, message: str, field: str = None, 
              value: Any = None, context: Dict[str, Any] = None) -> 'ValidationResult':
        """
        Create a failed validation result with a single error.
        
        Args:
            code: Error code
            message: Error message
            field: Optional field name
            value: Optional field value
            context: Optional error context
            
        Returns:
            Failed validation result with single error
        """
        error = ValidationError(
            code=code,
            message=message,
            field=field,
            value=value,
            context=context or {}
        )
        return cls(success=False, message=message, errors=[error])
    
    def add_error(self, code: str, message: str, field: str = None, 
                  value: Any = None, context: Dict[str, Any] = None) -> 'ValidationResult':
        """
        Add an error to this validation result.
        
        Args:
            code: Error code
            message: Error message
            field: Optional field name
            value: Optional field value
            context: Optional error context
            
        Returns:
            Self for chaining
        """
        error = ValidationError(
            code=code,
            message=message,
            field=field,
            value=value,
            context=context or {}
        )
        self.errors.append(error)
        self.success = False
        return self
    
    def add_warning(self, code: str, message: str, field: str = None,
                   value: Any = None, context: Dict[str, Any] = None) -> 'ValidationResult':
        """
        Add a warning to this validation result.
        
        Args:
            code: Warning code
            message: Warning message
            field: Optional field name
            value: Optional field value
            context: Optional warning context
            
        Returns:
            Self for chaining
        """
        warning = ValidationError(
            code=code,
            message=message,
            field=field,
            value=value,
            context=context or {}
        )
        self.warnings.append(warning)
        return self
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """
        Merge another validation result into this one.
        
        Args:
            other: Another validation result
            
        Returns:
            Self for chaining
        """
        if not other.success:
            self.success = False
        
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.context.update(other.context)
        
        # Update message if this was successful but other failed
        if self.message == "Validation passed" and not other.success:
            self.message = other.message
        
        return self
    
    @property
    def has_errors(self) -> bool:
        """Check if result has errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if result has warnings."""
        return len(self.warnings) > 0
    
    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Get number of warnings."""
        return len(self.warnings)
    
    def get_errors_by_code(self, code: str) -> List[ValidationError]:
        """
        Get errors by error code.
        
        Args:
            code: Error code to filter by
            
        Returns:
            List of errors with matching code
        """
        return [error for error in self.errors if error.code == code]
    
    def get_errors_by_field(self, field: str) -> List[ValidationError]:
        """
        Get errors by field name.
        
        Args:
            field: Field name to filter by
            
        Returns:
            List of errors for the specified field
        """
        return [error for error in self.errors if error.field == field]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert validation result to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'success': self.success,
            'message': self.message,
            'errors': [
                {
                    'code': error.code,
                    'message': error.message,
                    'field': error.field,
                    'value': error.value,
                    'context': error.context
                }
                for error in self.errors
            ],
            'warnings': [
                {
                    'code': warning.code,
                    'message': warning.message,
                    'field': warning.field,
                    'value': warning.value,
                    'context': warning.context
                }
                for warning in self.warnings
            ],
            'context': self.context,
            'timestamp': self.timestamp,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """
        Create validation result from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            ValidationResult instance
        """
        errors = [
            ValidationError(
                code=err['code'],
                message=err['message'],
                field=err.get('field'),
                value=err.get('value'),
                context=err.get('context', {})
            )
            for err in data.get('errors', [])
        ]
        
        warnings = [
            ValidationError(
                code=warn['code'],
                message=warn['message'],
                field=warn.get('field'),
                value=warn.get('value'),
                context=warn.get('context', {})
            )
            for warn in data.get('warnings', [])
        ]
        
        return cls(
            success=data['success'],
            message=data.get('message', ''),
            errors=errors,
            warnings=warnings,
            context=data.get('context', {}),
            timestamp=data.get('timestamp', time.time())
        )
    
    def __str__(self) -> str:
        """String representation for debugging."""
        status = "SUCCESS" if self.success else "FAILED"
        parts = [f"ValidationResult({status}): {self.message}"]
        
        if self.errors:
            parts.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                parts.append(f"  - {error}")
        
        if self.warnings:
            parts.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                parts.append(f"  - {warning}")
        
        return "\n".join(parts)
    
    def __bool__(self) -> bool:
        """Boolean conversion returns success status."""
        return self.success