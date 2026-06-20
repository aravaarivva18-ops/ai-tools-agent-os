import pytest

from tools.interaction_core import InteractionCore


def test_calculate_spring_physics():
    # Test valid spring physics calculations
    trajectory = InteractionCore.calculate_spring_physics(
        stiffness=170.0, damping=26.0, mass=1.0, duration_steps=50
    )
    assert len(trajectory) == 50
    assert all(isinstance(val, float) for val in trajectory)
    assert trajectory[0] >= 0.0


def test_calculate_spring_physics_invalid():
    # Test invalid parameter checks
    with pytest.raises(ValueError, match="Mass must be greater than zero"):
        InteractionCore.calculate_spring_physics(mass=0)
    with pytest.raises(ValueError, match="Stiffness must be greater than zero"):
        InteractionCore.calculate_spring_physics(stiffness=-10)
    with pytest.raises(ValueError, match="Damping cannot be negative"):
        InteractionCore.calculate_spring_physics(damping=-1)


def test_get_kowalski_preset():
    preset = InteractionCore.get_kowalski_preset("pop")
    assert preset["stiffness"] == 300.0
    assert preset["damping"] == 15.0
    assert "mass" in preset

    with pytest.raises(ValueError, match="Unknown preset name"):
        InteractionCore.get_kowalski_preset("invalid_preset")


def test_generate_ui_config():
    config = InteractionCore.generate_ui_config("snappy", "button")
    assert config["preset"] == "snappy"
    assert config["element_type"] == "button"
    assert "--spring-timing-curve" in config["css_variables"]
    assert len(config["best_practices"]) > 0
