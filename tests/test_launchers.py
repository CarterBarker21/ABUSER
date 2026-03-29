from pathlib import Path


def test_run_bat_has_pythonw_fallback_when_vbs_launcher_is_missing():
    run_bat = Path("run.bat").read_text(encoding="utf-8")

    assert "launcher.vbs" in run_bat
    assert "pythonw.exe" in run_bat
    assert "if exist" in run_bat.lower()
