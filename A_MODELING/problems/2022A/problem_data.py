"""Official 2022A parameters and auditable derived inertias (SI units)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import hypot, pi


@dataclass(frozen=True)
class PhysicalParameters:
    float_mass: float = 4866.0
    float_radius: float = 1.0
    cylinder_height: float = 3.0
    cone_height: float = 0.8
    oscillator_mass: float = 2433.0
    oscillator_radius: float = 0.5
    oscillator_height: float = 0.5
    seawater_density: float = 1025.0
    gravity: float = 9.8
    linear_spring_stiffness: float = 80000.0
    linear_spring_free_length: float = 0.5
    torsional_spring_stiffness: float = 250000.0
    hydrostatic_pitch_stiffness: float = 8890.7

    @property
    def hydrostatic_heave_stiffness(self) -> float:
        return self.seawater_density * self.gravity * pi * self.float_radius**2

    @property
    def equilibrium_spring_length(self) -> float:
        length = self.linear_spring_free_length - self.oscillator_mass * self.gravity / self.linear_spring_stiffness
        if length <= 0.0:
            raise ValueError("static spring compression exceeds its free length")
        return length

    @property
    def oscillator_axis_distance(self) -> float:
        return self.equilibrium_spring_length + 0.5 * self.oscillator_height

    @property
    def oscillator_centroid_pitch_inertia(self) -> float:
        return self.oscillator_mass * (3.0 * self.oscillator_radius**2 + self.oscillator_height**2) / 12.0

    @property
    def oscillator_pitch_inertia(self) -> float:
        return self.oscillator_centroid_pitch_inertia + self.oscillator_mass * self.oscillator_axis_distance**2

    def float_pitch_inertia_components(self) -> dict[str, float]:
        """Thin-shell area integration about the transverse axis at the separator."""
        radius = self.float_radius
        hc = self.cylinder_height
        hk = self.cone_height
        slant = hypot(radius, hk)
        areas = {
            "cylinder_side": 2.0 * pi * radius * hc,
            "cylinder_top": pi * radius**2,
            "cone_side": pi * radius * slant,
        }
        area_total = sum(areas.values())
        masses = {name: self.float_mass * area / area_total for name, area in areas.items()}
        inertias = {
            "cylinder_side": masses["cylinder_side"] * (0.5 * radius**2 + hc**2 / 3.0),
            "cylinder_top": masses["cylinder_top"] * (0.25 * radius**2 + hc**2),
            "cone_side": masses["cone_side"] * (0.25 * radius**2 + hk**2 / 6.0),
        }
        return {
            **{f"area_{name}_m2": value for name, value in areas.items()},
            **{f"mass_{name}_kg": value for name, value in masses.items()},
            **{f"inertia_{name}_kg_m2": value for name, value in inertias.items()},
            "total_kg_m2": sum(inertias.values()),
        }

    @property
    def float_pitch_inertia(self) -> float:
        return self.float_pitch_inertia_components()["total_kg_m2"]

    def audit_dict(self) -> dict[str, float]:
        values = asdict(self)
        values.update(
            hydrostatic_heave_stiffness=self.hydrostatic_heave_stiffness,
            equilibrium_spring_length=self.equilibrium_spring_length,
            oscillator_axis_distance=self.oscillator_axis_distance,
            oscillator_centroid_pitch_inertia=self.oscillator_centroid_pitch_inertia,
            oscillator_pitch_inertia=self.oscillator_pitch_inertia,
            float_pitch_inertia=self.float_pitch_inertia,
        )
        return values


@dataclass(frozen=True)
class WaveCase:
    name: str
    omega: float
    added_mass: float
    added_pitch_inertia: float
    radiation_heave_damping: float
    radiation_pitch_damping: float
    excitation_force: float
    excitation_moment: float

    @property
    def period(self) -> float:
        return 2.0 * pi / self.omega


PHYSICAL = PhysicalParameters()

WAVE_CASES = {
    1: WaveCase("Q1", 1.4005, 1335.535, 6779.315, 656.3616, 151.4388, 6250.0, 1230.0),
    2: WaveCase("Q2", 2.2143, 1165.992, 7131.290, 167.8395, 2992.724, 4890.0, 2560.0),
    3: WaveCase("Q3", 1.7152, 1028.876, 7001.914, 683.4558, 654.3383, 3640.0, 1690.0),
    4: WaveCase("Q4", 1.9806, 1091.099, 7142.493, 528.5018, 1655.909, 1760.0, 2140.0),
}


def wave_case(question: int) -> WaveCase:
    try:
        return WAVE_CASES[int(question)]
    except (KeyError, ValueError) as exc:
        raise ValueError("question must be 1, 2, 3, or 4") from exc

