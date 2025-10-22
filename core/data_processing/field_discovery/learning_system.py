"""
Field Discovery Learning System
================================

Machine learning system that improves field discovery accuracy over time
by learning from user validation feedback.
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationRecord:
    """Record of a field validation"""
    original_field_name: str
    discovered_standard_name: str
    corrected_standard_name: str
    was_correct: bool
    confidence_score: float
    timestamp: datetime
    feedback: Optional[str] = None
    patterns_matched: List[str] = None
    category: str = "unknown"


class FieldDiscoveryLearningSystem:
    """
    Learning system that improves field discovery accuracy through user feedback.

    Tracks validation history, identifies patterns in corrections, and adjusts
    discovery algorithms to improve future accuracy.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the learning system.

        Args:
            storage_path: Optional path to store learning data
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to project data directory
            self.storage_path = Path(__file__).parent.parent.parent.parent / 'data' / 'learning'

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.validation_file = self.storage_path / 'field_discovery_validations.json'

        # In-memory storage
        self.validation_history: List[ValidationRecord] = []
        self.field_accuracy: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_validations': 0,
            'correct_mappings': 0,
            'accuracy': 0.0,
            'common_corrections': defaultdict(int)
        })

        # Load existing data
        self._load_validation_history()

        logger.info(f"FieldDiscoveryLearningSystem initialized with {len(self.validation_history)} historical records")

    def record_validation(
        self,
        discovered_field: Any,  # DiscoveredField type
        correct_standard_name: str,
        feedback: Optional[str] = None
    ) -> None:
        """
        Record a validation event.

        Args:
            discovered_field: The discovered field that was validated
            correct_standard_name: The correct standard field name
            feedback: Optional user feedback
        """
        was_correct = (discovered_field.suggested_standard_name == correct_standard_name)

        record = ValidationRecord(
            original_field_name=discovered_field.original_name,
            discovered_standard_name=discovered_field.suggested_standard_name or "none",
            corrected_standard_name=correct_standard_name,
            was_correct=was_correct,
            confidence_score=discovered_field.confidence_score,
            timestamp=datetime.now(),
            feedback=feedback,
            patterns_matched=discovered_field.patterns_matched,
            category=discovered_field.category.value
        )

        # Add to history
        self.validation_history.append(record)

        # Update accuracy tracking
        self._update_accuracy_tracking(record)

        # Save to disk
        self._save_validation_history()

        logger.info(
            f"Recorded validation: '{record.original_field_name}' -> "
            f"'{record.corrected_standard_name}' (correct: {was_correct})"
        )

    def _update_accuracy_tracking(self, record: ValidationRecord) -> None:
        """Update accuracy metrics for a standard field name"""
        field = record.corrected_standard_name
        stats = self.field_accuracy[field]

        stats['total_validations'] += 1
        if record.was_correct:
            stats['correct_mappings'] += 1

        stats['accuracy'] = stats['correct_mappings'] / stats['total_validations']

        # Track common corrections
        if not record.was_correct:
            correction = f"{record.discovered_standard_name} -> {record.corrected_standard_name}"
            stats['common_corrections'][correction] += 1

    def get_historical_accuracy(self, standard_field_name: str) -> float:
        """
        Get historical accuracy for a specific standard field name.

        Args:
            standard_field_name: Standard field name

        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if standard_field_name in self.field_accuracy:
            return self.field_accuracy[standard_field_name]['accuracy']
        return 0.5  # Neutral score if no history

    def get_learned_mappings(self) -> Dict[str, str]:
        """
        Get learned mappings from validation history.

        Returns:
            Dictionary of original field names to standard field names
        """
        learned = {}

        for record in self.validation_history:
            if record.was_correct:
                learned[record.original_field_name] = record.corrected_standard_name

        return learned

    def suggest_correction(self, original_field_name: str) -> Optional[str]:
        """
        Suggest correction based on past validations.

        Args:
            original_field_name: Original field name to check

        Returns:
            Suggested standard field name if found in history
        """
        # Check exact matches first
        for record in reversed(self.validation_history):  # Most recent first
            if record.original_field_name == original_field_name:
                return record.corrected_standard_name

        # Check for similar field names
        normalized = original_field_name.lower().strip()
        for record in reversed(self.validation_history):
            if record.original_field_name.lower().strip() == normalized:
                return record.corrected_standard_name

        return None

    def get_pattern_accuracy(self, pattern: str) -> float:
        """
        Get accuracy of mappings that matched a specific pattern.

        Args:
            pattern: Pattern name to check

        Returns:
            Accuracy score (0.0 to 1.0)
        """
        matching_records = [
            r for r in self.validation_history
            if r.patterns_matched and pattern in r.patterns_matched
        ]

        if not matching_records:
            return 0.5  # Neutral if no data

        correct = sum(1 for r in matching_records if r.was_correct)
        return correct / len(matching_records)

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        if not self.validation_history:
            return {
                'total_validations': 0,
                'overall_accuracy': 0.0,
                'tracked_fields': 0
            }

        correct_validations = sum(1 for r in self.validation_history if r.was_correct)
        total_validations = len(self.validation_history)

        return {
            'total_validations': total_validations,
            'correct_validations': correct_validations,
            'overall_accuracy': correct_validations / total_validations,
            'tracked_fields': len(self.field_accuracy),
            'recent_accuracy': self._get_recent_accuracy(window=20)
        }

    def _get_recent_accuracy(self, window: int = 20) -> float:
        """Get accuracy of recent validations"""
        recent = self.validation_history[-window:]
        if not recent:
            return 0.0

        correct = sum(1 for r in recent if r.was_correct)
        return correct / len(recent)

    def _load_validation_history(self) -> None:
        """Load validation history from disk"""
        if not self.validation_file.exists():
            logger.info("No existing validation history found")
            return

        try:
            with open(self.validation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for record_data in data:
                # Convert timestamp string back to datetime
                record_data['timestamp'] = datetime.fromisoformat(record_data['timestamp'])

                record = ValidationRecord(**record_data)
                self.validation_history.append(record)

                # Rebuild accuracy tracking
                self._update_accuracy_tracking(record)

            logger.info(f"Loaded {len(self.validation_history)} validation records")

        except Exception as e:
            logger.error(f"Failed to load validation history: {e}")

    def _save_validation_history(self) -> None:
        """Save validation history to disk"""
        try:
            # Convert records to dicts
            records_data = []
            for record in self.validation_history:
                record_dict = asdict(record)
                # Convert datetime to ISO format string
                record_dict['timestamp'] = record.timestamp.isoformat()
                records_data.append(record_dict)

            with open(self.validation_file, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, indent=2)

            logger.debug(f"Saved {len(records_data)} validation records")

        except Exception as e:
            logger.error(f"Failed to save validation history: {e}")

    def export_training_data(self, output_path: Optional[Path] = None) -> Path:
        """
        Export validation history as training data for ML models.

        Args:
            output_path: Optional output file path

        Returns:
            Path to exported file
        """
        if not output_path:
            output_path = self.storage_path / 'training_data.json'

        training_data = []
        for record in self.validation_history:
            training_data.append({
                'input': record.original_field_name,
                'output': record.corrected_standard_name,
                'confidence': record.confidence_score,
                'patterns': record.patterns_matched,
                'category': record.category,
                'correct': record.was_correct
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2)

        logger.info(f"Exported training data to {output_path}")
        return output_path
