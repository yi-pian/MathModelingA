"""Transparent numerical checks; physical reasonableness remains a manual review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str = ""


class ValidationReport:
    def __init__(self):
        self.checks: list[Check] = []

    def add(self, name, passed=None, detail="", *, manual=False):
        status = "MANUAL CHECK REQUIRED" if manual else ("PASS" if bool(passed) else "FAIL")
        self.checks.append(Check(str(name), status, str(detail)))
        return self

    @property
    def passed(self):
        return all(check.status != "FAIL" for check in self.checks)

    def render(self):
        width = max([len(check.name) for check in self.checks] + [20])
        lines = ["========== VALIDATION REPORT =========="]
        lines.extend(f"{check.name:<{width}}  {check.status}" + (f"  {check.detail}" if check.detail else "") for check in self.checks)
        lines.append("=======================================")
        return "\n".join(lines)


def check_finite(values):
    array = np.asarray(values)
    return array.size > 0 and bool(np.all(np.isfinite(array)))


def check_nonempty(values):
    return np.asarray(values).size > 0


def check_bounds(values, lower, upper, *, tolerance=1e-10):
    values = np.asarray(values, float)
    return bool(np.all(values >= np.asarray(lower) - tolerance) and np.all(values <= np.asarray(upper) + tolerance))


def check_constraints(values: Iterable[float], *, sense="ge", tolerance=1e-8):
    values = np.asarray(list(values), float)
    if sense == "ge":
        return bool(np.all(values >= -tolerance))
    if sense == "le":
        return bool(np.all(values <= tolerance))
    if sense == "eq":
        return bool(np.all(np.abs(values) <= tolerance))
    raise ValueError("sense must be ge, le, or eq")


def check_monotonic_time(time, *, allow_equal=False):
    time = np.asarray(time, float)
    differences = np.diff(time)
    return time.size > 0 and check_finite(time) and bool(np.all(differences >= 0 if allow_equal else differences > 0))


def check_range(values, minimum=None, maximum=None):
    values = np.asarray(values, float)
    return check_finite(values) and (minimum is None or bool(np.all(values >= minimum))) and (maximum is None or bool(np.all(values <= maximum)))


def check_residual(residual, *, tolerance=1e-8):
    residual = np.asarray(residual, float)
    return check_finite(residual) and float(np.linalg.norm(residual.ravel(), ord=np.inf)) <= tolerance


def check_convergence(values, *, expected_order=None, ratio_limit=1.0):
    """Check successive error estimates decrease; optionally estimate positive order."""
    errors = np.asarray(values, float)
    decreasing = errors.size >= 2 and check_finite(errors) and np.all(errors[1:] <= errors[:-1] * ratio_limit)
    if expected_order is None or errors.size < 3 or np.any(errors <= 0):
        return bool(decreasing)
    estimated = np.log2(errors[:-1] / errors[1:])
    return bool(decreasing and np.median(estimated) >= expected_order * 0.5)


def standard_report(*, arrays=None, parameters=None, bounds=None, constraints=None, residual=None, time=None):
    report = ValidationReport()
    if arrays is not None:
        report.add("Finite values", check_finite(arrays)).add("Array nonempty", check_nonempty(arrays))
    if parameters is not None and bounds is not None:
        report.add("Parameter bounds", check_bounds(parameters, bounds[0], bounds[1]))
    if constraints is not None:
        report.add("Constraints", check_constraints(constraints))
    if residual is not None:
        report.add("Residual", check_residual(residual))
    if time is not None:
        report.add("Monotonic time", check_monotonic_time(time)).add("Duplicate time points", len(np.unique(time)) == len(time))
    report.add("Physical reasonableness", manual=True, detail="compare signs, magnitudes and conservation laws with the stated model")
    return report

