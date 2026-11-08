"""Teste pentru utilitarele de randare."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'render'))
import common  # noqa: E402


@pytest.mark.parametrize('weight, display', [('Regular', False), ('Medium', False), ('SemiBold', False), ('Bold', False),
                                             ('Regular', True), ('Medium', True), ('SemiBold', True), ('Bold', True)])
def test_inter_fonts_load_on_this_machine(weight, display):
    assert common.F(24, weight, display=display).getname()[0].startswith('Inter')
