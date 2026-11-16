"""Small, reproducible evaluation helpers for manually labeled fixtures."""

from collections.abc import Iterable
from dataclasses import dataclass

from job_market.processing.classification import classify_seniority
from job_market.processing.skill_extraction import extract_skills


@dataclass(frozen=True)
class LabeledPosting:
    title: str
    description: str
    expected_skills: frozenset[str]
    expected_seniority: str


@dataclass(frozen=True)
class EvaluationMetrics:
    skill_precision: float
    skill_recall: float
    skill_f1: float
    seniority_accuracy: float
    sample_size: int


def evaluate(records: Iterable[LabeledPosting]) -> EvaluationMetrics:
    records = list(records)
    if not records:
        raise ValueError("evaluation requires at least one labeled posting")
    true_positive = false_positive = false_negative = seniority_correct = 0
    for record in records:
        predicted = {item.canonical_skill for item in extract_skills(record.description)}
        true_positive += len(predicted & record.expected_skills)
        false_positive += len(predicted - record.expected_skills)
        false_negative += len(record.expected_skills - predicted)
        seniority, _, _ = classify_seniority(record.title, record.description)
        seniority_correct += seniority.value == record.expected_seniority
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return EvaluationMetrics(
        skill_precision=round(precision, 4),
        skill_recall=round(recall, 4),
        skill_f1=round(f1, 4),
        seniority_accuracy=round(seniority_correct / len(records), 4),
        sample_size=len(records),
    )
