# animation/set_profile.py
"""
Profile-to-style helpers.

Given a 3-element profile like ["Fire", "Water", "Light"],
this module returns a style dict describing the visual mood:
- name: human-readable style name
- base_colors: list of RGB colors used as the main spectrum
- pillar_width_factor: scales the width of the central aura pillar
- pillar_height_factor: scales the height of the pillar
- halo_scale: scales the halo around the "head"
- orb_count: number of orbiting orbs
- orb_radius_range: min / max radius for orbs (pixels)
- orb_speed_range: min / max angular speed
- orb_size_range: min / max orb radius (pixels)
- orb_vertical_squash: vertical squash factor for orbits (0.0~1.0)
"""

from typing import Dict, Any, List, Tuple

# Base element colors, kept in sync with AnimationEngine
ELEMENT_COLORS = {
    "Fire":   [(255, 120, 60), (255, 200, 90)],
    "Water":  [(60, 140, 255), (110, 220, 255)],
    "Wind":   [(190, 230, 255), (150, 210, 255)],
    "Earth":  [(90, 160, 100), (170, 220, 150)],
    "Light":  [(255, 255, 255), (255, 240, 210)],
    "Shadow": [(120, 70, 160), (60, 30, 100)],
}


def _lerp_color(c1, c2, t: float):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def normalize_profile(profile: List[str]) -> Tuple[str, str, str]:
    """
    Sort the profile so that ["Fire","Water","Light"] and
    ["Light","Water","Fire"] map to the same key.
    """
    return tuple(sorted(profile))


def _build_default_style(profile: List[str]) -> Dict[str, Any]:
    """
    Fallback style when a specific combination is not defined.
    Blend the three elements into a calm, balanced spectrum.
    """
    cols = []
    for name in profile:
        cols.extend(ELEMENT_COLORS.get(name, []))

    if not cols:
        base_colors = [(255, 255, 255), (200, 200, 200)]
    else:
        r = sum(c[0] for c in cols) // len(cols)
        g = sum(c[1] for c in cols) // len(cols)
        b = sum(c[2] for c in cols) // len(cols)
        avg = (r, g, b)

        cold_tint = _lerp_color(avg, (80, 150, 255), 0.35)
        warm_tint = _lerp_color(avg, (255, 200, 120), 0.35)
        base_colors = [cold_tint, avg, warm_tint]

    return {
        "name": "Balanced Spectrum",
        "base_colors": base_colors,
        "pillar_width_factor": 1.0,
        "pillar_height_factor": 1.0,
        "halo_scale": 1.0,
        "orb_count": 24,
        "orb_radius_range": (140, 260),
        "orb_speed_range": (0.3, 0.9),
        "orb_size_range": (4.0, 10.0),
        "orb_vertical_squash": 0.55,
    }


# --------------------------------------------------------------------
# PREDEFINED STYLES — tuned for emotional "feel"
# key = normalized 3-tuple of elements
# --------------------------------------------------------------------
SPECTRUM_STYLES: Dict[Tuple[str, str, str], Dict[str, Any]] = {
    # Warm, radiant, expansive: joy / confidence
    normalize_profile(["Fire", "Light", "Wind"]): {
        "name": "Solar Flare",
        "base_colors": [
            (255, 180, 90),   # warm gold
            (255, 230, 190),  # soft cream
            (255, 140, 80),   # orange accent
        ],
        "pillar_width_factor": 1.3,
        "pillar_height_factor": 1.1,
        "halo_scale": 1.3,
        "orb_count": 26,
        "orb_radius_range": (150, 280),
        "orb_speed_range": (0.5, 1.2),
        "orb_size_range": (5.0, 12.0),
        "orb_vertical_squash": 0.5,
    },

    # Calm, flowing, dreamy: healing / reflection
    normalize_profile(["Water", "Wind", "Light"]): {
        "name": "Aurora Tide",
        "base_colors": [
            (70, 160, 255),   # clear blue
            (140, 220, 255),  # cyan
            (230, 250, 255),  # pale blue-white
        ],
        "pillar_width_factor": 1.0,
        "pillar_height_factor": 1.2,
        "halo_scale": 1.4,
        "orb_count": 22,
        "orb_radius_range": (160, 260),
        "orb_speed_range": (0.25, 0.7),
        "orb_size_range": (4.0, 9.0),
        "orb_vertical_squash": 0.7,
    },

    # Deep, grounding, slow breathing: safety / stability
    normalize_profile(["Earth", "Water", "Light"]): {
        "name": "Forest Heart",
        "base_colors": [
            (70, 140, 110),   # deep green
            (160, 210, 150),  # soft leaf
            (230, 245, 220),  # misty light
        ],
        "pillar_width_factor": 1.1,
        "pillar_height_factor": 1.15,
        "halo_scale": 1.1,
        "orb_count": 20,
        "orb_radius_range": (140, 240),
        "orb_speed_range": (0.2, 0.6),
        "orb_size_range": (4.0, 11.0),
        "orb_vertical_squash": 0.6,
    },

    # Intense, electric, dramatic: anger / excitement / storm
    normalize_profile(["Fire", "Wind", "Shadow"]): {
        "name": "Storm Core",
        "base_colors": [
            (255, 120, 80),   # hot orange
            (170, 60, 200),   # magenta / violet
            (70, 80, 160),    # storm blue
        ],
        "pillar_width_factor": 1.4,
        "pillar_height_factor": 1.0,
        "halo_scale": 1.2,
        "orb_count": 28,
        "orb_radius_range": (160, 300),
        "orb_speed_range": (0.6, 1.5),
        "orb_size_range": (5.0, 13.0),
        "orb_vertical_squash": 0.5,
    },

    # Quiet, introspective, cosmic: mystery / melancholy
    normalize_profile(["Water", "Shadow", "Wind"]): {
        "name": "Nebula Veil",
        "base_colors": [
            (80, 110, 220),   # deep blue
            (120, 80, 190),   # violet
            (200, 180, 255),  # pale lavender
        ],
        "pillar_width_factor": 0.9,
        "pillar_height_factor": 1.25,
        "halo_scale": 1.5,
        "orb_count": 22,
        "orb_radius_range": (170, 280),
        "orb_speed_range": (0.25, 0.8),
        "orb_size_range": (3.5, 9.0),
        "orb_vertical_squash": 0.65,
    },

    # Very bright, pure, almost angelic: clarity / hope
    normalize_profile(["Light", "Wind", "Earth"]): {
        "name": "Dawn Bloom",
        "base_colors": [
            (255, 255, 255),  # pure light
            (240, 255, 210),  # pale greenish white
            (255, 220, 170),  # warm highlight
        ],
        "pillar_width_factor": 1.0,
        "pillar_height_factor": 1.3,
        "halo_scale": 1.5,
        "orb_count": 20,
        "orb_radius_range": (150, 250),
        "orb_speed_range": (0.25, 0.7),
        "orb_size_range": (4.0, 10.0),
        "orb_vertical_squash": 0.6,
    },

    # Heavy, grounded, slightly dark: burden / contemplation
    normalize_profile(["Earth", "Water", "Shadow"]): {
        "name": "Deep Root",
        "base_colors": [
            (50, 110, 90),    # dark green
            (100, 160, 140),  # teal
            (200, 230, 210),  # soft mist
        ],
        "pillar_width_factor": 1.2,
        "pillar_height_factor": 0.95,
        "halo_scale": 1.0,
        "orb_count": 18,
        "orb_radius_range": (130, 230),
        "orb_speed_range": (0.2, 0.55),
        "orb_size_range": (4.0, 9.0),
        "orb_vertical_squash": 0.5,
    },

    # Sharp, hot, aggressive: strong will / conflict
    normalize_profile(["Fire", "Earth", "Shadow"]): {
        "name": "Magma Pulse",
        "base_colors": [
            (255, 120, 70),   # lava
            (200, 90, 60),    # dark lava
            (80, 30, 70),     # deep magma
        ],
        "pillar_width_factor": 1.4,
        "pillar_height_factor": 0.9,
        "halo_scale": 1.1,
        "orb_count": 26,
        "orb_radius_range": (150, 260),
        "orb_speed_range": (0.5, 1.3),
        "orb_size_range": (5.0, 12.0),
        "orb_vertical_squash": 0.45,
    },

    # Playful, light, floating: curiosity / optimism
    normalize_profile(["Fire", "Light", "Earth"]): {
        "name": "Lantern Garden",
        "base_colors": [
            (255, 190, 120),  # warm peach
            (230, 240, 200),  # pale yellow
            (180, 210, 150),  # soft green
        ],
        "pillar_width_factor": 1.1,
        "pillar_height_factor": 1.15,
        "halo_scale": 1.3,
        "orb_count": 24,
        "orb_radius_range": (130, 240),
        "orb_speed_range": (0.3, 0.8),
        "orb_size_range": (4.5, 11.0),
        "orb_vertical_squash": 0.7,
    },
}


def get_spectrum_style(profile: List[str]) -> Dict[str, Any]:
    """
    Entry point used by the animation engine.

    Given a profile list like ["Water", "Fire", "Light"],
    return a style dict. If the specific combination is
    not defined, return a reasonable default.
    """
    if not profile or len(profile) == 0:
        # No profile yet → neutral default
        return {
            "name": "None",
            "base_colors": [(255, 255, 255), (200, 200, 200)],
            "pillar_width_factor": 1.0,
            "pillar_height_factor": 1.0,
            "halo_scale": 1.0,
            "orb_count": 24,
            "orb_radius_range": (140, 260),
            "orb_speed_range": (0.3, 0.9),
            "orb_size_range": (4.0, 10.0),
            "orb_vertical_squash": 0.55,
        }

    key = normalize_profile(profile)
    if key in SPECTRUM_STYLES:
        return SPECTRUM_STYLES[key]

    # Fallback: blended but still structured style
    return _build_default_style(profile)

