from types import SimpleNamespace

from cbpi4_BrewStart.step_match import (
    is_matching_step_active,
    parse_step_kind,
    step_matches,
    step_matches_preset,
)


def test_mash_preset_matches_bm_mash():
    step = SimpleNamespace(type="BM_MashStep", name="Rast 1")
    assert step_matches_preset(step, ("Mash",)) is True
    assert step_matches(step, "", "", step_kind="Mash") is True


def test_boil_preset_matches_boil_step():
    step = SimpleNamespace(type="BoilStep", name="Kochen")
    assert step_matches(step, "", "", step_kind="Boil") is True
    assert step_matches(step, "", "", step_kind="Mash") is False


def test_whirlpool_by_name_on_wait_step():
    step = SimpleNamespace(type="WaitStep", name="Whirlpool 15min")
    assert step_matches(step, "", "", step_kind="Whirlpool") is True
    assert step_matches(step, "", "", step_kind="Boil") is False


def test_mash_or_boil():
    mash = SimpleNamespace(type="MashStep", name="x")
    boil = SimpleNamespace(type="BM_BoilStep", name="y")
    wait = SimpleNamespace(type="WaitStep", name="Pause")
    assert step_matches(mash, "", "", step_kind="Mash or Boil") is True
    assert step_matches(boil, "", "", step_kind="Mash or Boil") is True
    assert step_matches(wait, "", "", step_kind="Mash or Boil") is False


def test_all_three_kinds():
    whirl = SimpleNamespace(type="NotificationStep", name="Whirlpool")
    assert step_matches(whirl, "", "", step_kind="Mash+Boil+Whirlpool") is True


def test_custom_comma_list():
    step = SimpleNamespace(type="BoilStep", name="x")
    assert (
        step_matches(step, "TypeContains", "mash,boil", step_kind="Custom") is True
    )


def test_custom_type_or_name():
    step = SimpleNamespace(type="WaitStep", name="Whirlpool")
    assert (
        step_matches(step, "TypeOrNameContains", "whirlpool", step_kind="Custom")
        is True
    )


def test_parse_step_kind():
    assert parse_step_kind("Boil") == ("Boil",)
    assert parse_step_kind("Mash or Boil") == ("Mash", "Boil")
    assert parse_step_kind("Custom") == ()


def test_is_matching_step_active_with_controller():
    step = SimpleNamespace(type="BoilStep", name="Hopfenkochen")

    class Ctrl:
        def find_by_status(self, status):
            if status == "A":
                return step
            return None

    assert is_matching_step_active(Ctrl(), "", "", step_kind="Boil") is True
    assert is_matching_step_active(Ctrl(), "", "", step_kind="Whirlpool") is False
