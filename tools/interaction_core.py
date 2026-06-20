from typing import Any


class InteractionCore:
    """
    Interaction Core implementing Emil Kowalski's micro-interaction guidelines
    and spring physics math for high-quality UI animations.
    """

    @staticmethod
    def calculate_spring_physics(
        stiffness: float = 170.0,
        damping: float = 26.0,
        mass: float = 1.0,
        initial_velocity: float = 0.0,
        duration_steps: int = 100,
        time_step: float = 0.016,  # ~60fps step duration in seconds
    ) -> list[float]:
        """
        Calculates spring trajectory using Hooke's Law and Euler integration.
        F = -k*x - c*v (where k is stiffness, c is damping, x is displacement).
        Returns a list of displacement steps from 0.0 (start) to 1.0 (target).
        """
        if mass <= 0:
            raise ValueError("Mass must be greater than zero.")
        if stiffness <= 0:
            raise ValueError("Stiffness must be greater than zero.")
        if damping < 0:
            raise ValueError("Damping cannot be negative.")

        x = -1.0  # Start at -1.0 so target is 0.0 (displacement reaches 0)
        v = initial_velocity
        trajectory = []

        for _ in range(duration_steps):
            # Spring force
            f_spring = -stiffness * x
            # Damping force
            f_damping = -damping * v
            # Acceleration
            a = (f_spring + f_damping) / mass
            # Integrate velocity & position
            v += a * time_step
            x += v * time_step

            # Map displacement from [-1.0, 0.0] to [0.0, 1.0] for ease of CSS use
            normalized_val = min(max(x + 1.0, 0.0), 1.5)
            trajectory.append(round(normalized_val, 4))

        return trajectory

    @staticmethod
    def get_kowalski_preset(preset_name: str) -> dict[str, Any]:
        """Returns pre-calibrated spring physics parameters based on Emil Kowalski's presets."""
        presets = {
            "pop": {
                "stiffness": 300.0,
                "damping": 15.0,
                "mass": 0.8,
                "description": "Energetic scale up/down with subtle overshoot",
            },
            "smooth": {
                "stiffness": 120.0,
                "damping": 20.0,
                "mass": 1.0,
                "description": "Highly dampened elegant slide/fade transition",
            },
            "snappy": {
                "stiffness": 210.0,
                "damping": 20.0,
                "mass": 0.5,
                "description": "Quick UI responses like switches or tabs",
            },
            "bouncy": {
                "stiffness": 180.0,
                "damping": 12.0,
                "mass": 1.0,
                "description": "Playful spring response with noticeable overshoot",
            },
        }

        selected = presets.get(preset_name.lower())
        if not selected:
            raise ValueError(
                f"Unknown preset name: {preset_name}. Available: {list(presets.keys())}"
            )
        return selected

    @classmethod
    def generate_ui_config(
        cls, preset_name: str, element_type: str = "button"
    ) -> dict[str, Any]:
        """
        Generates full CSS / Tailwind UI configuration block including Spring parameters,
        motion blur, scale limits and performance tip comments.
        """
        preset = cls.get_kowalski_preset(preset_name)
        trajectory = cls.calculate_spring_physics(
            stiffness=preset["stiffness"],
            damping=preset["damping"],
            mass=preset["mass"],
        )

        # Calculate ideal motion blur filter strength based on speed/damping profile
        # Snappy animations can afford higher blur to feel smooth, smooth animations need less.
        max_velocity = max(
            abs(trajectory[i] - trajectory[i - 1]) for i in range(1, len(trajectory))
        )
        blur_strength = round(max_velocity * 40, 2)

        config = {
            "preset": preset_name,
            "element_type": element_type,
            "physics": {
                "stiffness": preset["stiffness"],
                "damping": preset["damping"],
                "mass": preset["mass"],
            },
            "css_variables": {
                "--spring-duration": "0.35s",
                "--spring-timing-curve": f"linear({', '.join(map(str, trajectory))})",
                "--motion-blur": f"blur({blur_strength}px)",
                "--scale-active": "0.95" if element_type == "button" else "1.0",
            },
            "best_practices": [
                "Always apply 'will-change: transform' to avoid layout shifts",
                "Ensure transition-property is limited to transform and opacity",
                "Use hardware accelerated composite layers",
            ],
        }
        return config
