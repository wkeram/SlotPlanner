"""Input validation system for SlotPlanner application.

This module provides comprehensive validation for all user inputs
including teachers, children, tandems, and settings.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from app.config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any validation warnings."""
        return len(self.warnings) > 0
    
    def get_error_message(self) -> str:
        """Get formatted error message for display."""
        if not self.has_errors:
            return ""
        return "\n".join(self.errors)
    
    def get_warning_message(self) -> str:
        """Get formatted warning message for display."""
        if not self.has_warnings:
            return ""
        return "\n".join(self.warnings)


class Validator:
    """Main validation class for all application data."""
    
    # Time constants
    MIN_SLOT_DURATION = 45  # minutes
    TIME_RASTER = 15  # 15-minute intervals
    WORK_DAY_START = 7  # 7:00 AM
    WORK_DAY_END = 20  # 8:00 PM
    
    # Days of week
    VALID_DAYS = ["Mo", "Di", "Mi", "Do", "Fr"]
    
    @staticmethod
    def validate_teacher_name(name: str) -> ValidationResult:
        """Validate teacher name input.
        
        Args:
            name: Teacher name to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Basic checks
        if not name or not name.strip():
            errors.append("Teacher name cannot be empty")
        elif len(name.strip()) < 2:
            errors.append("Teacher name must be at least 2 characters long")
        elif len(name.strip()) > 50:
            errors.append("Teacher name cannot exceed 50 characters")
        
        # Character validation
        cleaned_name = name.strip()
        if not re.match(r'^[a-zA-ZäöüÄÖÜß\s\-_.]+$', cleaned_name):
            errors.append("Teacher name can only contain letters, spaces, hyphens, underscores, and dots")
        
        # Check for reserved words
        reserved_words = ["admin", "system", "default", "none", "null"]
        if cleaned_name.lower() in reserved_words:
            errors.append(f"'{cleaned_name}' is a reserved name and cannot be used")
        
        # Warnings
        if cleaned_name != name:
            warnings.append("Leading/trailing whitespace will be removed")
        
        if any(char in cleaned_name for char in ["_", "."]):
            warnings.append("Underscores and dots in names may cause display issues")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_time_slot(start_time: str, end_time: str) -> ValidationResult:
        """Validate a time slot for teachers or children.
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Format validation
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        
        if not re.match(time_pattern, start_time):
            errors.append(f"Invalid start time format: '{start_time}'. Use HH:MM format")
        
        if not re.match(time_pattern, end_time):
            errors.append(f"Invalid end time format: '{end_time}'. Use HH:MM format")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        try:
            # Parse times
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            
            # Basic time logic validation
            if start_dt >= end_dt:
                errors.append("End time must be after start time")
            
            # Duration validation
            duration = (end_dt - start_dt).total_seconds() / 60
            if duration < Validator.MIN_SLOT_DURATION:
                errors.append(f"Time slot must be at least {Validator.MIN_SLOT_DURATION} minutes long")
            
            # Working hours validation
            work_start = datetime.strptime(f"{Validator.WORK_DAY_START:02d}:00", "%H:%M")
            work_end = datetime.strptime(f"{Validator.WORK_DAY_END:02d}:00", "%H:%M")
            
            if start_dt < work_start:
                warnings.append(f"Start time {start_time} is before typical working hours ({Validator.WORK_DAY_START:02d}:00)")
            
            if end_dt > work_end:
                warnings.append(f"End time {end_time} is after typical working hours ({Validator.WORK_DAY_END:02d}:00)")
            
            # Time raster validation
            for time_str, time_dt, label in [(start_time, start_dt, "Start"), (end_time, end_dt, "End")]:
                if time_dt.minute % Validator.TIME_RASTER != 0:
                    warnings.append(f"{label} time {time_str} is not aligned with {Validator.TIME_RASTER}-minute raster")
            
            # Duration warnings
            if duration > 480:  # 8 hours
                warnings.append("Time slot longer than 8 hours may indicate an error")
            
        except ValueError as e:
            errors.append(f"Error parsing time values: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_teacher_availability(availability: Dict[str, List[List[str]]]) -> ValidationResult:
        """Validate complete teacher availability data.
        
        Args:
            availability: Dictionary with days as keys and time slot lists as values
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        if not availability or all(not slots for slots in availability.values()):
            errors.append("Teacher must have at least one available time slot")
            return ValidationResult(is_valid=False, errors=errors)
        
        total_hours = 0
        has_valid_slots = False
        
        for day, slots in availability.items():
            # Validate day
            if day not in Validator.VALID_DAYS:
                errors.append(f"Invalid day: '{day}'. Valid days are: {', '.join(Validator.VALID_DAYS)}")
                continue
            
            if not slots:
                continue  # Empty day is okay, just skip
            
            day_slots = []
            day_duration = 0
            
            # Validate each slot
            for slot in slots:
                if len(slot) != 2:
                    errors.append(f"Invalid slot format for day '{day}': {slot}")
                    continue
                
                start_time, end_time = slot
                slot_validation = Validator.validate_time_slot(start_time, end_time)
                
                if not slot_validation.is_valid:
                    # Add specific time slot errors with day context
                    for error in slot_validation.errors:
                        errors.append(f"Day '{day}': {error}")
                    continue
                else:
                    has_valid_slots = True
                
                # Track for overlap detection
                try:
                    start_dt = datetime.strptime(start_time, "%H:%M")
                    end_dt = datetime.strptime(end_time, "%H:%M")
                    day_slots.append((start_dt, end_dt))
                    day_duration += (end_dt - start_dt).total_seconds() / 3600  # hours
                except ValueError:
                    continue
            
            # Check for overlapping slots
            day_slots.sort()
            for i in range(len(day_slots) - 1):
                if day_slots[i][1] > day_slots[i + 1][0]:
                    errors.append(f"Overlapping time slots on day '{day}': {day_slots[i]} and {day_slots[i + 1]}")
            
            total_hours += day_duration
            
            # Day-specific warnings
            if day_duration > 10:
                warnings.append(f"Day '{day}' has {day_duration:.1f} hours of availability (more than 10 hours)")
            elif day_duration < 2:
                warnings.append(f"Day '{day}' has only {day_duration:.1f} hours of availability")
        
        # Check if at least one valid slot exists
        if not has_valid_slots:
            errors.append("Teacher must have at least one valid time slot (minimum 45 minutes)")
        
        # Overall availability warnings
        if total_hours > 0:
            if total_hours < 5:
                warnings.append(f"Total weekly availability is only {total_hours:.1f} hours (quite low)")
            elif total_hours > 40:
                warnings.append(f"Total weekly availability is {total_hours:.1f} hours (more than 40 hours)")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_child_name(name: str) -> ValidationResult:
        """Validate child name input.
        
        Args:
            name: Child name to validate
            
        Returns:
            ValidationResult with validation status
        """
        # Child names have same validation rules as teacher names
        return Validator.validate_teacher_name(name)
    
    @staticmethod
    def validate_optimization_weights(weights: Dict[str, int]) -> ValidationResult:
        """Validate optimization weight settings.
        
        Args:
            weights: Dictionary of weight names and values
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        expected_weights = {
            "preferred_teacher": (0, 20),
            "priority_early_slot": (0, 20),
            "tandem_fulfilled": (0, 20),
            "teacher_pause_respected": (0, 20),
            "preserve_existing_plan": (0, 20)
        }
        
        # Check for missing weights
        for weight_name, (min_val, max_val) in expected_weights.items():
            if weight_name not in weights:
                errors.append(f"Missing optimization weight: {weight_name}")
                continue
            
            value = weights[weight_name]
            
            # Type validation
            if not isinstance(value, int):
                errors.append(f"Weight '{weight_name}' must be an integer, got {type(value).__name__}")
                continue
            
            # Range validation
            if value < min_val or value > max_val:
                errors.append(f"Weight '{weight_name}' must be between {min_val} and {max_val}, got {value}")
            
            # Logical warnings
            if weight_name == "preserve_existing_plan" and value < 5:
                warnings.append("Low 'preserve existing plan' weight may cause significant schedule changes")
            
            if weight_name == "preferred_teacher" and value == 0:
                warnings.append("Zero 'preferred teacher' weight will ignore teacher preferences")
        
        # Check for unexpected weights
        for weight_name in weights:
            if weight_name not in expected_weights:
                warnings.append(f"Unknown optimization weight: {weight_name}")
        
        # Overall balance check
        total_weight = sum(weights.get(name, 0) for name in expected_weights.keys())
        if total_weight == 0:
            errors.append("At least one optimization weight must be greater than zero")
        elif total_weight < 10:
            warnings.append("Very low total weights may produce poor optimization results")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_tandem_pair(child1_name: str, child2_name: str, priority: int) -> ValidationResult:
        """Validate tandem pair configuration.
        
        Args:
            child1_name: First child name
            child2_name: Second child name  
            priority: Tandem priority (1-10)
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Name validation
        child1_validation = Validator.validate_child_name(child1_name)
        child2_validation = Validator.validate_child_name(child2_name)
        
        if not child1_validation.is_valid:
            errors.extend([f"Child 1: {error}" for error in child1_validation.errors])
        
        if not child2_validation.is_valid:
            errors.extend([f"Child 2: {error}" for error in child2_validation.errors])
        
        # Same child check
        if child1_name.strip().lower() == child2_name.strip().lower():
            errors.append("Tandem cannot contain the same child twice")
        
        # Priority validation
        if not isinstance(priority, int):
            errors.append(f"Priority must be an integer, got {type(priority).__name__}")
        elif priority < 1 or priority > 10:
            errors.append("Priority must be between 1 and 10")
        elif priority < 3:
            warnings.append("Low priority tandems may not be scheduled together")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


def validate_ui_input(widget, input_type: str, **kwargs) -> ValidationResult:
    """Validate input from UI widgets.
    
    Args:
        widget: Qt widget containing the input
        input_type: Type of validation to perform
        **kwargs: Additional parameters for validation
        
    Returns:
        ValidationResult with validation status
    """
    try:
        if input_type == "teacher_name":
            from PySide6.QtWidgets import QLineEdit
            if isinstance(widget, QLineEdit):
                return Validator.validate_teacher_name(widget.text())
        
        elif input_type == "time_slot":
            # Expects kwargs: start_widget, end_widget
            start_widget = kwargs.get("start_widget")
            end_widget = kwargs.get("end_widget")
            
            if start_widget and end_widget:
                return Validator.validate_time_slot(
                    start_widget.currentText(),
                    end_widget.currentText()
                )
        
        # Add more UI validation types as needed
        
        return ValidationResult(
            is_valid=False,
            errors=[f"Unknown validation type: {input_type}"]
        )
        
    except Exception as e:
        logger.error(f"Error in UI validation: {e}")
        return ValidationResult(
            is_valid=False,
            errors=[f"Validation error: {str(e)}"]
        )