# animation/set_profile.py
"""
Profile-to-style helpers.

Given a 3-element profile like ["Fire", "Water", "Light"],
this module returns a style dict describing the visual mood.
"""

from typing import Dict, Any, List, Tuple

# Base element colors, should be consistent with AnimationEngine
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
    Blend the elements into a calm, balanced spectrum and
    provide default geometric parameters.
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
        "pattern_type": "pillar_orbs",
    }


# --------------------------------------------------------------------
# PRESETS: for each 3-element combination, define name + pattern type
# and optionally override some geometry parameters.
# We always start from _build_default_style and then overlay these.
# --------------------------------------------------------------------

PATTERN_PRESETS: Dict[Tuple[str, str, str], Dict[str, Any]] = {}


def _add_preset(elems, name, pattern_type, **overrides):
    key = normalize_profile(list(elems))
    data: Dict[str, Any] = {
        "name": name,
        "pattern_type": pattern_type,
    }
    data.update(overrides)
    PATTERN_PRESETS[key] = data


# Earth, Fire, Light, Shadow, Water, Wind
E, F, L, S, W, D = "Earth", "Fire", "Light", "Shadow", "Water", "Wind"

# 1. Earth Fire Light
_add_preset(
    (E, F, L),
    name="Lantern Core",
    pattern_type="pillar_orbs",
    pillar_width_factor=1.2,
    pillar_height_factor=1.1,
    halo_scale=1.3,
    orb_count=26,
)

# 2. Earth Fire Shadow
_add_preset(
    (E, F, S),
    name="Magma Root",
    pattern_type="radial_rays",
)

# 3. Earth Fire Water
_add_preset(
    (E, F, W),
    name="Steam Bloom",
    pattern_type="ring_waves",
)

# 4. Earth Fire Wind
_add_preset(
    (E, F, D),
    name="Dustflare",
    pattern_type="radial_rays",
)

# 5. Earth Light Shadow
_add_preset(
    (E, L, S),
    name="Twilight Ground",
    pattern_type="galaxy",
)

# 6. Earth Light Water
_add_preset(
    (E, L, W),
    name="Forest Heart",
    pattern_type="pillar_orbs",
    pillar_height_factor=1.15,
)

# 7. Earth Light Wind
_add_preset(
    (E, L, D),
    name="Dawn Breeze",
    pattern_type="ring_waves",
)

# 8. Earth Shadow Water
_add_preset(
    (E, S, W),
    name="Deep Spring",
    pattern_type="galaxy",
)

# 9. Earth Shadow Wind
_add_preset(
    (E, S, D),
    name="Hollow Gale",
    pattern_type="radial_rays",
)

# 10. Earth Water Wind
_add_preset(
    (E, W, D),
    name="Valley Mist",
    pattern_type="ring_waves",
)

# 11. Fire Light Shadow
_add_preset(
    (F, L, S),
    name="Solar Eclipse",
    pattern_type="radial_rays",
)

# 12. Fire Light Water
_add_preset(
    (F, L, W),
    name="Aurora Flame",
    pattern_type="ring_waves",
)

# 13. Fire Light Wind
_add_preset(
    (F, L, D),
    name="Solar Flare",
    pattern_type="pillar_orbs",
    orb_count=28,
)

# 14. Fire Shadow Water
_add_preset(
    (F, S, W),
    name="Boiling Night",
    pattern_type="galaxy",
)

# 15. Fire Shadow Wind
_add_preset(
    (F, S, D),
    name="Storm Core",
    pattern_type="radial_rays",
)

# 16. Fire Water Wind
_add_preset(
    (F, W, D),
    name="Tempest Rise",
    pattern_type="ring_waves",
)

# 17. Light Shadow Water
_add_preset(
    (L, S, W),
    name="Moonlit Tide",
    pattern_type="ring_waves",
)

# 18. Light Shadow Wind
_add_preset(
    (L, S, D),
    name="Starlit Veil",
    pattern_type="galaxy",
)

# 19. Light Water Wind
_add_preset(
    (L, W, D),
    name="Sky Lanterns",
    pattern_type="pillar_orbs",
    halo_scale=1.4,
)

# 20. Shadow Water Wind
_add_preset(
    (S, W, D),
    name="Nebula Drift",
    pattern_type="galaxy",
)


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
            "pattern_type": "pillar_orbs",
        }

    default_style = _build_default_style(profile)
    key = normalize_profile(profile)
    preset = PATTERN_PRESETS.get(key)
    if preset:
        # Overlay preset values onto the default style
        for k, v in preset.items():
            default_style[k] = v

    return default_style
