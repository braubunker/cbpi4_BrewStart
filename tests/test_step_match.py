from types import SimpleNamespace

from cbpi4_BrewStart.step_match import is_matching_step_active, step_matches


def test_type_contains_mash():
    step = SimpleNamespace(type="BM_MashStep", name="Einmaischen")
    assert step_matches(step, "TypeContains", "mash") is True
    assert step_matches(step, "TypeContains", "boil") is False


def test_type_contains_default_mash_when_empty():
    step = SimpleNamespace(type="MashInStep", name="x")
    assert step_matches(step, "TypeContains", "") is True


def test_any_active():
    step = SimpleNamespace(type="DatetimeWaitStep", name="Wait")
    assert step_matches(step, "AnyActive", "") is True


def test_name_contains():
    step = SimpleNamespace(type="X", name="Hauptguss Maische")
    assert step_matches(step, "NameContains", "maische") is True


def test_is_matching_step_active_with_controller():
    step = SimpleNamespace(type="BM_MashStep", name="Rast 1")

    class Ctrl:
        def find_by_status(self, status):
            if status == "A":
                return step
            return None

    assert is_matching_step_active(Ctrl(), "TypeContains", "Mash") is True
    assert is_matching_step_active(Ctrl(), "TypeContains", "Boil") is False
    assert is_matching_step_active(None, "AnyActive", "") is False
