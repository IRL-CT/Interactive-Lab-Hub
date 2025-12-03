# animation/set_profile.py
"""
Profile-to-style helpers.

Given a 3-element profile like ["Fire", "Water", "Light"],
this module returns a style dict describing the visual mood.

We also assign each profile a pattern_type:
- pillar_orbs
- ring_waves
- radial_rays
- galaxy
- double_pillar
- vertical_ribbons
- grid_pulse
- starfield
- vortex
- cross_waves
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
        "orb_count": 32,
        "orb_radius_range": (160, 320),
        "orb_speed_range": (0.4, 1.0),
        "orb_size_range": (5.0, 12.0),
        "orb_vertical_squash": 0.55,
        "pattern_type": "pillar_orbs",
    }


# --------------------------------------------------------------------
# PRESETS: for each 3-element combination, define:
# - name: energy field name
# - pattern_type: which visual pattern is used
# plus optional overrides of geometric parameters.
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


# Short aliases
E, F, L, S, Wa, Wi = "Earth", "Fire", "Light", "Shadow", "Water", "Wind"

# 20 combinations → distribute across 10+ pattern types

# 1. Earth Fire Light
_add_preset(
    (E, F, L),
    name="Lantern Core",
    pattern_type="pillar_orbs",
    pillar_width_factor=1.3,
    pillar_height_factor=1.1,
    halo_scale=1.4,
)

# 2. Earth Fire Shadow
_add_preset(
    (E, F, S),
    name="Magma Root",
    pattern_type="radial_rays",
)

# 3. Earth Fire Water
_add_preset(
    (E, F, Wa),
    name="Steam Bloom",
    pattern_type="ring_waves",
)

# 4. Earth Fire Wind
_add_preset(
    (E, F, Wi),
    name="Dustflare",
    pattern_type="vortex",
)

# 5. Earth Light Shadow
_add_preset(
    (E, L, S),
    name="Twilight Ground",
    pattern_type="double_pillar",
)

# 6. Earth Light Water
_add_preset(
    (E, L, Wa),
    name="Forest Heart",
    pattern_type="pillar_orbs",
    pillar_height_factor=1.2,
)

# 7. Earth Light Wind
_add_preset(
    (E, L, Wi),
    name="Dawn Breeze",
    pattern_type="vertical_ribbons",
)

# 8. Earth Shadow Water
_add_preset(
    (E, S, Wa),
    name="Deep Spring",
    pattern_type="galaxy",
)

# 9. Earth Shadow Wind
_add_preset(
    (E, S, Wi),
    name="Hollow Gale",
    pattern_type="cross_waves",
)

# 10. Earth Water Wind
_add_preset(
    (E, Wa, Wi),
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
    (F, L, Wa),
    name="Aurora Flame",
    pattern_type="vortex",
)

# 13. Fire Light Wind
_add_preset(
    (F, L, Wi),
    name="Solar Flare",
    pattern_type="pillar_orbs",
)

# 14. Fire Shadow Water
_add_preset(
    (F, S, Wa),
    name="Boiling Night",
    pattern_type="starfield",
)

# 15. Fire Shadow Wind
_add_preset(
    (F, S, Wi),
    name="Storm Core",
    pattern_type="radial_rays",
)

# 16. Fire Water Wind
_add_preset(
    (F, Wa, Wi),
    name="Tempest Rise",
    pattern_type="cross_waves",
)

# 17. Light Shadow Water
_add_preset(
    (L, S, Wa),
    name="Moonlit Tide",
    pattern_type="ring_waves",
)

# 18. Light Shadow Wind
_add_preset(
    (L, S, Wi),
    name="Starlit Veil",
    pattern_type="galaxy",
)

# 19. Light Water Wind
_add_preset(
    (L, Wa, Wi),
    name="Sky Lanterns",
    pattern_type="double_pillar",
)

# 20. Shadow Water Wind
_add_preset(
    (S, Wa, Wi),
    name="Nebula Drift",
    pattern_type="grid_pulse",
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
            "orb_count": 32,
            "orb_radius_range": (160, 320),
            "orb_speed_range": (0.4, 1.0),
            "orb_size_range": (5.0, 12.0),
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
