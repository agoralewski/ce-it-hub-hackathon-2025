Translations are automatically generated.

You need to have gettext installed (https://www.drupal.org/docs/8/modules/potion/how-to-install-setup-gettext).

Then, run the following commands.

```sh
uv run python manage.py makemessages -l en -l pl
uv run python manage.py compilemessages -l en -l pl
```