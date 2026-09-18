from typer.testing import CliRunner

from shaktimaan.cli import app

runner = CliRunner()


def test_version_flag_prints_version_and_exits_zero():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "shaktimaan" in result.stdout.lower()
