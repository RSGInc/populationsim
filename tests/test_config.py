import pytest

from populationsim.core.config import validate_settings


@pytest.mark.parametrize(
    ("plural_setting", "singular_setting"),
    [
        ("absolute_upper_bounds", "absolute_upper_bound"),
        ("absolute_lower_bounds", "absolute_lower_bound"),
    ],
)
def test_validate_settings_rejects_plural_absolute_bounds(
    plural_setting, singular_setting
):
    with pytest.raises(RuntimeError, match=singular_setting):
        validate_settings({plural_setting: 1})
