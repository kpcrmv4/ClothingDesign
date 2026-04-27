"""Size chart for baby clothing patterns (0-24 months). All measurements in cm."""

SIZE_CHART = {
    "0-3m":  {"chest": 41, "length": 30, "waist": 42, "hip": 44, "back_w": 18,
              "shoulder": 6.5, "neck_circ": 23, "arm_len": 16, "rise_f": 14,
              "rise_b": 16, "head": 38, "strap_len": 16, "ruffle_h": 6},
    "3-6m":  {"chest": 43, "length": 33, "waist": 44, "hip": 46, "back_w": 19,
              "shoulder": 7.0, "neck_circ": 24, "arm_len": 18, "rise_f": 15,
              "rise_b": 17, "head": 42, "strap_len": 18, "ruffle_h": 7},
    "6-9m":  {"chest": 45, "length": 36, "waist": 46, "hip": 48, "back_w": 20,
              "shoulder": 7.5, "neck_circ": 25, "arm_len": 20, "rise_f": 16,
              "rise_b": 18, "head": 44, "strap_len": 20, "ruffle_h": 8},
    "9-12m": {"chest": 47, "length": 39, "waist": 48, "hip": 50, "back_w": 21,
              "shoulder": 8.0, "neck_circ": 26, "arm_len": 22, "rise_f": 17,
              "rise_b": 19, "head": 46, "strap_len": 22, "ruffle_h": 9},
    "12-18m":{"chest": 49, "length": 42, "waist": 50, "hip": 52, "back_w": 22,
              "shoulder": 8.5, "neck_circ": 27, "arm_len": 24, "rise_f": 18,
              "rise_b": 20, "head": 48, "strap_len": 24, "ruffle_h": 10},
    "18-24m":{"chest": 51, "length": 45, "waist": 52, "hip": 54, "back_w": 23,
              "shoulder": 9.0, "neck_circ": 28, "arm_len": 26, "rise_f": 19,
              "rise_b": 21, "head": 49, "strap_len": 26, "ruffle_h": 11},
}


def get_size(size_label: str) -> dict:
    """Return size spec dict or raise ValueError."""
    if size_label not in SIZE_CHART:
        raise ValueError(
            f"size '{size_label}' not found. Available: {list(SIZE_CHART)}"
        )
    return SIZE_CHART[size_label]
