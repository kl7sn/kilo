# Contributing

Repo: [kl7sn/kilo](https://github.com/kl7sn/kilo). License: [MIT](LICENSE).

## Desktop

```bash
pip install -r view/requirements.txt
python3 view/app.py --root /path/to/Projects
```

Do not commit `view/dist/` or `view/build/`. Pack locally with `python3 view/pack.py`.

Version lives in `view/VERSION`. Patch the third number for small fixes; bump the second for features.

## Skill

Keep `skills/kilo/SKILL.md` short. Long rules go in `skills/kilo/protocols/`.

## Pull requests

- Match the surrounding code: Python stdlib server, no Electron, no npm for the board.
- The board is a viewer + Orca launcher. It should not write kilo protocol files except display alias YAML and the vault session-map JSON.
