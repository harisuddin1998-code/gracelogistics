"""Helpers for reading form values without ever rejecting a blank field.

Every helper accepts a missing key, an empty string or garbage and returns a safe
value instead of raising, so a form can always be saved even if the user left
everything empty.

Conventions used by the controllers:
  * free text                      -> ''      (form_text)
  * unique / CHECK-limited columns -> None    (form_text_or_none)  NULLs never collide
  * money / quantity / odometer    -> 0       (form_float / form_int)
  * optional numbers               -> None    (form_float_or_none / form_int_or_none)
  * dates                          -> None    (form_date)
  * foreign keys (vehicle, driver) -> None    (form_id)
"""


def _clean(form, key):
    value = form.get(key)
    if value is None:
        return ''
    return str(value).strip()


def form_text(form, key, default=''):
    """Stripped text, or `default` when blank/missing."""
    value = _clean(form, key)
    return value if value else default


def form_text_or_none(form, key):
    """Stripped text, or None when blank/missing."""
    value = _clean(form, key)
    return value if value else None


def form_float_or_none(form, key):
    value = _clean(form, key).replace(',', '')
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def form_float(form, key, default=0.0):
    value = form_float_or_none(form, key)
    return default if value is None else value


def form_int_or_none(form, key):
    value = form_float_or_none(form, key)
    return None if value is None else int(value)


def form_int(form, key, default=0):
    value = form_int_or_none(form, key)
    return default if value is None else value


def form_id(form, key):
    """Foreign-key id (vehicle_id, driver_id ...) or None when nothing selected."""
    return form_int_or_none(form, key)


def form_date(form, key):
    """Date string (YYYY-MM-DD as sent by <input type=date>) or None."""
    return form_text_or_none(form, key)
