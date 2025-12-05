from typing import List, Dict, Tuple

Color = Tuple[int, int, int]
Style = Dict[str, object]

# ----------------------------------------------------------------------
# Base element color palette (primary hues)
# ----------------------------------------------------------------------

ELEMENT_MAIN_COLOR: Dict[str, Color] = {
    "Fire":   (255, 130, 70),
    "Water":  (80, 160, 255),
    "Wind":   (190, 230, 255),
    "Earth":  (110, 180, 110),
    "Light":  (255, 255, 230),
    "Shadow": (150, 110, 200),
}

ELEMENT_SECONDARY_COLOR: Dict[str, Color] = {
    "Fire":   (255, 210, 120),
    "Water":  (120, 220, 255),
    "Wind":   (150, 210, 255),
    "Earth":  (170, 220, 150),
    "Light":  (255, 245, 210),
    "Shadow": (90, 60, 140),
}

# Slightly different dark backgrounds to give each profile a distinct
# "night atmosphere" while still looking consistent.
BASE_BACKGROUNDS: Dict[str, Color] = {
    "Fire":   (10, 4, 8),
    "Water":  (3, 8, 16),
    "Wind":   (3, 10, 18),
    "Earth":  (5, 10, 6),
    "Light":  (8, 8, 18),
    "Shadow": (6, 4, 10),
}

# Global default background if nothing else is set
DEFAULT_BG: Color = (5, 7, 18)


def make_style(
    name: str,
    pattern_type: str,
    base_colors: List[Color],
    background_color: Color = DEFAULT_BG,
    **kwargs,
) -> Style:
    """Helper to create a style dict."""
    style: Style = {
        "name": name,
        "pattern_type": pattern_type,
        "base_colors": base_colors,
        "background_color": background_color,
    }
    style.update(kwargs)
    return style


def element_pair_palette(elem: str) -> List[Color]:
    """Return a simple 2-color palette for a single element."""
    c1 = ELEMENT_MAIN_COLOR.get(elem, (255, 255, 255))
    c2 = ELEMENT_SECONDARY_COLOR.get(elem, c1)
    return [c1, c2]


def combo_palette(elems: List[str]) -> List[Color]:
    """
    Return a 3-color palette for a 3-element combination.
    The order of elems is already sorted by caller.
    """
    colors: List[Color] = []
    for e in elems:
        colors.append(ELEMENT_MAIN_COLOR.get(e, (255, 255, 255)))
    return colors


# ----------------------------------------------------------------------
# Single-element styles (fallback before 3-element profile is locked)
# ----------------------------------------------------------------------

SINGLE_ELEMENT_STYLES: Dict[str, Style] = {
    "Fire": make_style(
        name="Inner Flame",
        pattern_type="pillar_orbs",
        base_colors=element_pair_palette("Fire"),
        background_color=BASE_BACKGROUNDS["Fire"],
        pillar_width_factor=1.1,
        halo_scale=1.3,
        orb_count=40,
    ),
    "Water": make_style(
        name="Tidal Heart",
        pattern_type="ring_waves",
        base_colors=element_pair_palette("Water"),
        background_color=BASE_BACKGROUNDS["Water"],
    ),
    "Wind": make_style(
        name="Sky Drift",
        pattern_type="vortex",
        base_colors=element_pair_palette("Wind"),
        background_color=BASE_BACKGROUNDS["Wind"],
    ),
    "Earth": make_style(
        name="Root Pulse",
        pattern_type="double_pillar",
        base_colors=element_pair_palette("Earth"),
        background_color=BASE_BACKGROUNDS["Earth"],
    ),
    "Light": make_style(
        name="Stellar Bloom",
        pattern_type="starfield",
        base_colors=element_pair_palette("Light"),
        background_color=BASE_BACKGROUNDS["Light"],
    ),
    "Shadow": make_style(
        name="Night Current",
        pattern_type="galaxy",
        base_colors=element_pair_palette("Shadow"),
        background_color=BASE_BACKGROUNDS["Shadow"],
    ),
}

# ----------------------------------------------------------------------
# 3-element combination styles (20 total)
#
# Key (always sorted): ("Earth", "Fire", "Light"), etc.
# ----------------------------------------------------------------------

COMBO_STYLES: Dict[Tuple[str, str, str], Style] = {}

# 1. Earth, Fire, Light
COMBO_STYLES[("Earth", "Fire", "Light")] = make_style(
    name="Solar Grove",
    pattern_type="double_pillar",
    base_colors=combo_palette(["Earth", "Fire", "Light"]),
    background_color=(12, 6, 8),
    pillar_width_factor=1.2,
    pillar_height_factor=1.1,
    halo_scale=1.4,
)

# 2. Earth, Fire, Shadow
COMBO_STYLES[("Earth", "Fire", "Shadow")] = make_style(
    name="Magma Veil",
    pattern_type="vortex",
    base_colors=combo_palette(["Fire", "Earth", "Shadow"]),
    background_color=(10, 3, 10),
)

# 3. Earth, Fire, Water
COMBO_STYLES[("Earth", "Fire", "Water")] = make_style(
    name="Molten Delta",
    pattern_type="cross_waves",
    base_colors=combo_palette(["Fire", "Water", "Earth"]),
    background_color=(6, 9, 12),
)

# 4. Earth, Fire, Wind
COMBO_STYLES[("Earth", "Fire", "Wind")] = make_style(
    name="Blazing Gale",
    pattern_type="comet_trails",
    base_colors=combo_palette(["Fire", "Wind", "Earth"]),
    background_color=(10, 5, 8),
)

# 5. Earth, Light, Shadow
COMBO_STYLES[("Earth", "Light", "Shadow")] = make_style(
    name="Twilight Garden",
    pattern_type="blooming_orbs",
    base_colors=combo_palette(["Light", "Earth", "Shadow"]),
    background_color=(6, 6, 12),
)

# 6. Earth, Light, Water
COMBO_STYLES[("Earth", "Light", "Water")] = make_style(
    name="Crystal Spring",
    pattern_type="ring_waves",
    base_colors=combo_palette(["Water", "Light", "Earth"]),
    background_color=(4, 8, 14),
)

# 7. Earth, Light, Wind
COMBO_STYLES[("Earth", "Light", "Wind")] = make_style(
    name="Daybreak Breeze",
    pattern_type="vertical_ribbons",
    base_colors=combo_palette(["Wind", "Light", "Earth"]),
    background_color=(6, 9, 16),
)

# 8. Earth, Shadow, Water
COMBO_STYLES[("Earth", "Shadow", "Water")] = make_style(
    name="Deep Moss",
    pattern_type="grid_pulse",
    base_colors=combo_palette(["Earth", "Water", "Shadow"]),
    background_color=(4, 7, 9),
)

# 9. Earth, Shadow, Wind
COMBO_STYLES[("Earth", "Shadow", "Wind")] = make_style(
    name="Fogbound Roots",
    pattern_type="aurora",
    base_colors=combo_palette(["Shadow", "Wind", "Earth"]),
    background_color=(5, 6, 10),
)

# 10. Earth, Water, Wind
COMBO_STYLES[("Earth", "Water", "Wind")] = make_style(
    name="Mist Valley",
    pattern_type="spiral_rings",
    base_colors=combo_palette(["Water", "Wind", "Earth"]),
    background_color=(3, 8, 12),
)

# 11. Fire, Light, Shadow
COMBO_STYLES[("Fire", "Light", "Shadow")] = make_style(
    name="Lunar Flame",
    pattern_type="galaxy",
    base_colors=combo_palette(["Fire", "Light", "Shadow"]),
    background_color=(10, 5, 12),
)

# 12. Fire, Light, Water
COMBO_STYLES[("Fire", "Light", "Water")] = make_style(
    name="Radiant Tide",
    pattern_type="ring_waves",
    base_colors=combo_palette(["Fire", "Water", "Light"]),
    background_color=(5, 8, 13),
)

# 13. Fire, Light, Wind
COMBO_STYLES[("Fire", "Light", "Wind")] = make_style(
    name="Solar Storm",
    pattern_type="radial_rays",
    base_colors=combo_palette(["Fire", "Light", "Wind"]),
    background_color=(12, 7, 10),
)

# 14. Fire, Shadow, Water
COMBO_STYLES[("Fire", "Shadow", "Water")] = make_style(
    name="Abyss Ember",
    pattern_type="vortex",
    base_colors=combo_palette(["Shadow", "Fire", "Water"]),
    background_color=(6, 4, 10),
)

# 15. Fire, Shadow, Wind
COMBO_STYLES[("Fire", "Shadow", "Wind")] = make_style(
    name="Nocturne Blaze",
    pattern_type="comet_trails",
    base_colors=combo_palette(["Shadow", "Fire", "Wind"]),
    background_color=(8, 5, 11),
)

# 16. Fire, Water, Wind
COMBO_STYLES[("Fire", "Water", "Wind")] = make_style(
    name="Storm Current",
    pattern_type="pillar_orbs",
    base_colors=combo_palette(["Fire", "Wind", "Water"]),
    background_color=(5, 9, 14),
    pillar_width_factor=0.9,
    halo_scale=1.6,
    orb_count=50,
)

# 17. Light, Shadow, Water
COMBO_STYLES[("Light", "Shadow", "Water")] = make_style(
    name="Moonlit Lake",
    pattern_type="starfield",
    base_colors=combo_palette(["Light", "Water", "Shadow"]),
    background_color=(3, 7, 13),
)

# 18. Light, Shadow, Wind
COMBO_STYLES[("Light", "Shadow", "Wind")] = make_style(
    name="Veil of Dawn",
    pattern_type="aurora",
    base_colors=combo_palette(["Light", "Shadow", "Wind"]),
    background_color=(6, 6, 12),
)

# 19. Light, Water, Wind
COMBO_STYLES[("Light", "Water", "Wind")] = make_style(
    name="Crystal Sky",
    pattern_type="spiral_rings",
    base_colors=combo_palette(["Light", "Wind", "Water"]),
    background_color=(4, 9, 16),
)

# 20. Shadow, Water, Wind
COMBO_STYLES[("Shadow", "Water", "Wind")] = make_style(
    name="Midnight Surge",
    pattern_type="blooming_orbs",
    base_colors=combo_palette(["Shadow", "Water", "Wind"]),
    background_color=(4, 5, 10),
)


# ----------------------------------------------------------------------
# Default / fallback style
# ----------------------------------------------------------------------

DEFAULT_STYLE: Style = make_style(
    name="Idle Constellation",
    pattern_type="pillar_orbs",
    base_colors=[(200, 200, 220), (150, 180, 220)],
    background_color=DEFAULT_BG,
    pillar_width_factor=1.0,
    halo_scale=1.0,
    orb_count=30,
)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def _normalize_profile(profile: List[str]) -> List[str]:
    """Return a sorted list of unique element names."""
    unique = sorted(set(profile))
    return unique


def get_spectrum_style(profile: List[str] | None) -> Style:
    """
    Map a list of elements (length 0–3) to a style dict.

    Cases:
      - [] or None         → neutral default style
      - [E]                → single-element style
      - [E1, E2]           → blended 2-element style (uses DEFAULT_STYLE-like pattern)
      - [E1, E2, E3]       → 3-element combination, one of 20 styles
    """
    if profile is None:
        profile = []

    if len(profile) == 0:
        return DEFAULT_STYLE

    profile = _normalize_profile(profile)

    # Single element
    if len(profile) == 1:
        elem = profile[0]
        return SINGLE_ELEMENT_STYLES.get(elem, DEFAULT_STYLE)

    # Three elements → check combo table
    if len(profile) >= 3:
        key = tuple(profile[:3])
        style = COMBO_STYLES.get(key)
        if style:
            return style
        # Fallback if not found for any reason:
        return make_style(
            name="Unknown Constellation",
            pattern_type="pillar_orbs",
            base_colors=combo_palette(list(key)),
            background_color=DEFAULT_BG,
        )

    # Exactly 2 elements → simple blended style
    if len(profile) == 2:
        e1, e2 = profile
        colors = [
            ELEMENT_MAIN_COLOR.get(e1, (255, 255, 255)),
            ELEMENT_MAIN_COLOR.get(e2, (220, 220, 255)),
        ]
        return make_style(
            name=f"{e1} · {e2} Field",
            pattern_type="ring_waves",
            base_colors=colors,
            background_color=DEFAULT_BG,
        )

    # Should never reach here, but keep a safe fallback
    return DEFAULT_STYLE
