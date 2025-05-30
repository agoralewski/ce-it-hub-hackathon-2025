# Preventing Specific Phrases from Being Translated in Django

This document explains how to prevent specific phrases (like "krwinkowy system prezentowy") from being translated in a Django project.

## Background

In Django's internationalization (i18n) system, all text wrapped in translation markers (like `{% trans "text" %}` or `gettext("text")`) is extracted and translated according to the locale. However, sometimes you want certain phrases to remain unchanged across all languages.

## Methods to Prevent Translation

### 1. Using the Script (Recommended)

We've created a script that fixes translation files to ensure "krwinkowy system prezentowy" is never translated:

```bash
./scripts/manage_django.sh fix_translations
```

This script:
- Scans all .po translation files
- Identifies entries containing "krwinkowy system prezentowy" (case-insensitive)
- Ensures these strings remain unchanged in all translations
- Compiles the messages so changes take effect

### 2. For Future Development (In Code)

If you're adding new strings that should not be translated:

#### Method A: Mark as "do not translate"

Use HTML comments before the string:

```html
<!-- xgettext:no-python-format -->
{% trans "krwinkowy system prezentowy" %}
```

#### Method B: Use Django's `mark_safe` and String Concatenation

```python
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# Translatable part
translatable = _("Welcome to the")

# Non-translatable part (will be preserved as-is)
non_translatable = "Krwinkowy System Prezentowy"

# Combine them
message = mark_safe(f"{translatable} {non_translatable}")
```

#### Method C: Use `ngettext` with Context

```python
from django.utils.translation import pgettext

# The context helps translators understand this shouldn't be translated
message = pgettext("brand_name_do_not_translate", "Krwinkowy System Prezentowy")
```

## Best Practices

1. Keep a list of all phrases that should never be translated in a central location
2. Use consistent casing for the phrases
3. Run the fix script after updating translation files
4. Add notes for translators when applicable

## Troubleshooting

If you notice the phrase is still being translated:

1. Check if the string appears in multiple variations (case, punctuation, etc.)
2. Run the fix script again
3. Clear your browser cache
4. Restart the Django development server

If problems persist, check the `.po` files manually and verify the phrase is properly preserved.
