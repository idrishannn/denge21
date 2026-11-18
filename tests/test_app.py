"""Uygulamanın uçtan uca açıldığını doğrulayan smoke testleri."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

def total(at):
    return next(m.value for m in at.metric if m.label == "Tamamlanan görev")


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_runs_on_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGE21_DB", str(tmp_path / "fresh.db"))
    monkeypatch.delenv("DENGE21_DEMO", raising=False)
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert total(at) == "0 / 126"


def test_demo_mode_is_seeded_and_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGE21_DEMO", "1")
    monkeypatch.setenv("DENGE21_DB", str(tmp_path / "must_not_exist.db"))
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert total(at) != "0 / 126"
    assert not (tmp_path / "must_not_exist.db").exists()


def test_checking_a_task_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("DENGE21_DB", str(tmp_path / "x.db"))
    monkeypatch.delenv("DENGE21_DEMO", raising=False)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.checkbox[0].check().run()
    assert not at.exception
    assert total(at) == "1 / 126"
