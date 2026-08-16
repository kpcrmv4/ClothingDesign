"""
Smoke tests for the Baby Fashion Engine.

Runs with pytest (`pytest test_smoke.py -q`) or standalone
(`python test_smoke.py`) so it works even without pytest installed.

What it guards:
  * every pattern generates a PDF + preview PNG + rendered PNG, in every size
  * the shopping-list fabric figure equals the cutting-layout figure
    (these lived in two hand-maintained copies of the geometry and had
    silently drifted apart)
  * every registered pattern is reachable from every renderer
  * keyword matching does not confuse กางเกงใน/กางเกง or ชุดหมีคอระบาย/ชุดหมี
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customize
import cutting_layout
import features
import geometry
import preview
import rendered
from patterns import (dress, tiered_dress, bib, bloomers, bonnet, kimono_top,
                      pants, tshirt, romper, sleep_sack, flutter_romper)
from sizes import SIZE_CHART

GENERATORS = {
    "dress": dress.generate,
    "tiered_dress": tiered_dress.generate,
    "bib": bib.generate,
    "bloomers": bloomers.generate,
    "bonnet": bonnet.generate,
    "kimono_top": kimono_top.generate,
    "pants": pants.generate,
    "tshirt": tshirt.generate,
    "romper": romper.generate,
    "sleep_sack": sleep_sack.generate,
    "flutter_romper": flutter_romper.generate,
}

SAMPLE_SIZES = ["0-3m", "6-9m", "18-24m"]


# ============================================================
# Registry consistency
# ============================================================
def test_every_pattern_is_registered():
    assert set(GENERATORS) == set(features.PATTERN_META), (
        "PATTERN_META and the generator list disagree: "
        f"{set(GENERATORS) ^ set(features.PATTERN_META)}")


def test_metadata_is_complete():
    required = {"title", "title_th", "emoji", "difficulty", "time_hours",
                "fabric_types", "notions", "pieces"}
    for key, meta in features.PATTERN_META.items():
        missing = required - set(meta)
        assert not missing, f"{key} missing metadata fields: {missing}"


def test_every_pattern_has_geometry():
    for key in features.PATTERN_META:
        pieces = geometry.get_pieces(key, "6-9m")
        assert pieces, f"{key} returned no pieces"
        for p in pieces:
            assert p["w"] > 0 and p["h"] > 0, f"{key}: bad piece {p}"
            assert p["count"] >= 1, f"{key}: bad count in {p}"


# ============================================================
# The bug this file exists to prevent
# ============================================================
def test_fabric_estimate_matches_cutting_layout():
    """The shopping list and the layout PNG must quote the same length."""
    for key in features.PATTERN_META:
        for width in (90, 115, 150):
            pieces = geometry.get_pieces(key, "6-9m")
            _, packed_len, _ = geometry.pack_pieces(pieces, width)
            estimate = geometry.estimate_fabric(key, "6-9m", width)
            assert abs(estimate - packed_len * 1.10) < 1e-6, (
                f"{key} @ {width}cm: estimate {estimate} != "
                f"packed {packed_len} + 10%")


def test_fabric_estimate_is_sane():
    """A baby garment should never need more than a few metres of fabric."""
    for key in features.PATTERN_META:
        for size in SAMPLE_SIZES:
            est = geometry.estimate_fabric(key, size, 115)
            assert 10 < est < 400, (
                f"{key} @ {size}: {est:.0f}cm looks wrong")


def test_wider_fabric_never_needs_more_length():
    for key in features.PATTERN_META:
        lengths = [geometry.estimate_fabric(key, "12-18m", w)
                   for w in (90, 115, 150)]
        assert lengths[0] >= lengths[1] - 1e-6 >= lengths[2] - 1e-6, (
            f"{key}: wider bolt needs more length: {lengths}")


# ============================================================
# Generation
# ============================================================
def _check_outputs(key, size, out, gen, **kwargs):
    result = gen(size, output_dir=out, **kwargs)
    assert not result.startswith("Error"), f"{key} {size}: {result}"

    pdfs = [f for f in os.listdir(out) if f.endswith(".pdf")]
    assert pdfs, f"{key} {size}: no PDF produced"
    assert os.path.getsize(os.path.join(out, pdfs[0])) > 1000, (
        f"{key} {size}: PDF suspiciously small")

    p = preview.generate_preview(key, size, output_dir=out)
    assert os.path.exists(p), f"{key} {size}: preview missing"
    r = rendered.render_finished(key, size, output_dir=out)
    assert os.path.exists(r), f"{key} {size}: rendered image missing"


def test_all_patterns_generate():
    for key, gen in GENERATORS.items():
        for size in SAMPLE_SIZES:
            with tempfile.TemporaryDirectory() as out:
                _check_outputs(key, size, out, gen)


def test_all_sizes_generate_for_one_pattern():
    """Catch a size-chart entry that breaks a formula."""
    for size in SIZE_CHART:
        with tempfile.TemporaryDirectory() as out:
            _check_outputs("tiered_dress", size, out, tiered_dress.generate)


def test_pattern_style_options():
    cases = [
        ("dress", dress.generate, {"skirt_style": "bubble"}),
        ("dress", dress.generate, {"front_placket": True}),
        ("dress", dress.generate,
         {"skirt_style": "bubble", "front_placket": True}),
        ("tiered_dress", tiered_dress.generate,
         {"tiers": 2, "neckline": "halter"}),
        ("tiered_dress", tiered_dress.generate,
         {"tiers": 3, "neckline": "strap", "lace_trim": False}),
        ("tiered_dress", tiered_dress.generate,
         {"tiers": 3, "neckline": "round", "tier_fullness": 2.2}),
        ("pants", pants.generate, {"style": "short"}),
        ("tshirt", tshirt.generate, {"sleeve": "long"}),
        ("flutter_romper", flutter_romper.generate, {"ruffle_height": 9.0}),
    ]
    for key, gen, kwargs in cases:
        with tempfile.TemporaryDirectory() as out:
            result = gen("9-12m", output_dir=out, **kwargs)
            assert not result.startswith("Error"), f"{key} {kwargs}: {result}"
            assert [f for f in os.listdir(out) if f.endswith(".pdf")], (
                f"{key} {kwargs}: no PDF")


def test_cutting_layout_generates():
    for key in features.PATTERN_META:
        with tempfile.TemporaryDirectory() as out:
            p = cutting_layout.generate_layout(key, "6-9m", 115,
                                               output_dir=out)
            assert not p.startswith("Error"), f"{key}: {p}"
            assert os.path.exists(p)


def test_output_dir_is_respected():
    """No generator may write into the process cwd."""
    with tempfile.TemporaryDirectory() as out:
        before = set(os.listdir("."))
        dress.generate("3-6m", output_dir=out)
        tiered_dress.generate("3-6m", output_dir=out)
        after = set(os.listdir("."))
        assert before == after, f"leaked files into cwd: {after - before}"


# ============================================================
# Invalid input must return a message, never raise
# ============================================================
def test_invalid_options_return_error_strings():
    with tempfile.TemporaryDirectory() as out:
        assert dress.generate("3-6m", skirt_style="poof",
                              output_dir=out).startswith("Error")
        assert tiered_dress.generate("3-6m", neckline="v-neck",
                                     output_dir=out).startswith("Error")
        assert tiered_dress.generate("3-6m", tiers=5,
                                     output_dir=out).startswith("Error")
        assert pants.generate("3-6m", style="capri",
                              output_dir=out).startswith("Error")


def test_invalid_size_reports_cleanly():
    assert "ไม่พบไซส์" in features.format_fabric_requirement("dress", "5y")
    assert "ไม่พบไซส์" in features.generate_shopping_list(["dress"], "5y")
    assert "ไม่รู้จัก" in features.generate_shopping_list(["tuxedo"], "3-6m")


# ============================================================
# Description matching
# ============================================================
def test_specific_keywords_beat_generic_substrings():
    cases = [
        ("อยากได้กางเกงในเด็ก", "bloomers", "pants"),
        ("ชุดหมีคอระบายน่ารัก", "flutter_romper", "romper"),
        ("เดรสกระโปรงชั้นลายตาราง", "tiered_dress", "dress"),
    ]
    for text, expected, must_not_win in cases:
        matches = customize._score_matches(text.lower())
        assert matches, f"no match for {text!r}"
        winner = matches[0][0]
        assert winner == expected, (
            f"{text!r} matched {winner}, expected {expected}")
        assert must_not_win not in [m[0] for m in matches], (
            f"{text!r} should not also match {must_not_win}")


def test_description_infers_style_params():
    out = customize.suggest_pattern_from_description(
        "เดรสกระโปรงชั้น คอผูกหลัง ผูกโบว์ 3 ชั้น")
    assert "tiered_dress" in out
    assert "neckline='halter'" in out

    out = customize.suggest_pattern_from_description("เดรสชายบอลลูน ติดกระดุมหน้า")
    assert "skirt_style='bubble'" in out
    assert "front_placket=True" in out

    out = customize.suggest_pattern_from_description("กางเกงขาสั้นใส่หน้าร้อน")
    assert "style='short'" in out


def test_customize_rejects_params_the_pattern_does_not_take():
    out = customize.customize_pattern("pants", "6-9m", {"neckline": "halter"})
    assert "ใช้กับ" in out and "ไม่ได้" in out
    out = customize.customize_pattern("tiered_dress", "6-9m",
                                      {"neckline": "halter", "tiers": 2})
    assert "neckline='halter'" in out and "tiers=2" in out


# ============================================================
# Standalone runner
# ============================================================
def _main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as e:
            failed.append((name, e))
            print(f"  FAIL {name}\n       {e}")
        except Exception as e:
            failed.append((name, e))
            print(f"  ERR  {name}\n       {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_main())
