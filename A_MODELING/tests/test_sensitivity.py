import numpy as np

from core.sensitivity import finite_difference_sensitivity, multi_parameter_sensitivity, normalized_sensitivity, one_parameter_sensitivity


def test_percent_perturbations_and_finite_difference():
    model = lambda p: p["a"] * p["b"] ** 2
    table = one_parameter_sensitivity(model, {"a": 2.0, "b": 3.0}, "a", changes=(-0.1, 0, 0.1))
    assert list(table["change_rate"]) == [-0.1, 0.0, 0.1]
    assert np.allclose(table["output"], [16.2, 18.0, 19.8])
    combined = multi_parameter_sensitivity(model, {"a": 2.0, "b": 3.0})
    assert set(combined["parameter"]) == {"a", "b"}
    function = lambda x: x[0] ** 2 + 3 * x[1]
    assert np.allclose(finite_difference_sensitivity(function, [2, 4]), [4, 3], atol=1e-7)
    assert np.allclose(normalized_sensitivity(function, [2, 4]), [0.5, 0.75], atol=1e-6)
