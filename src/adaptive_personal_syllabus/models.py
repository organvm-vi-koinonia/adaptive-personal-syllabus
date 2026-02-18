"""Domain models for adaptive personal syllabus."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class LearnerProfile:
    """A learner's interests and progress."""

    name: str
    organs_of_interest: list[str] = field(default_factory=list)  # e.g., ["I", "II", "V"]
    level: DifficultyLevel = DifficultyLevel.BEGINNER
    completed_modules: list[str] = field(default_factory=list)

    total_modules: int = 0  # set after path generation for accurate progress

    @property
    def progress_pct(self) -> float:
        if not self.completed_modules:
            return 0.0
        if self.total_modules > 0:
            return min(100.0, len(self.completed_modules) / self.total_modules * 100.0)
        # Fallback when total is unknown: cap at 100%
        return min(100.0, len(self.completed_modules) * 10.0)


@dataclass
class LearningModule:
    """A single learning module in a syllabus path."""

    module_id: str
    title: str
    organ: str  # which organ this belongs to
    difficulty: DifficultyLevel
    readings: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    estimated_hours: float = 2.0
    prerequisites: list[str] = field(default_factory=list)  # module_ids


@dataclass
class LearningPath:
    """A personalized sequence of learning modules."""

    path_id: str
    title: str
    learner: LearnerProfile
    modules: list[LearningModule] = field(default_factory=list)

    @property
    def total_hours(self) -> float:
        return sum(m.estimated_hours for m in self.modules)

    @property
    def module_count(self) -> int:
        return len(self.modules)

    def next_module(self) -> LearningModule | None:
        for m in self.modules:
            if m.module_id not in self.learner.completed_modules:
                return m
        return None
