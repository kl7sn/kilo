# GitHub Release notes (template)

Tag from `view/VERSION` (currently 0.2.3). Upload `view/dist/Kilo.app` as a zip. Do not claim notarization.

## Title

`Kilo v0.2.3`

## Body

Kilo is a local board for a `Projects/` folder, plus the `/kilo` process skill.

### Desktop (macOS, Apple Silicon)

1. Download `Kilo.app.zip`, unzip, move to Applications.
2. First open: System Settings → Privacy & Security → Open Anyway. The app is ad-hoc signed, not notarized.
3. Pick a `Projects/` folder, or an empty folder to initialize one.
4. Optional: install [Orca](https://www.onorca.dev/docs/install) for sessions and new lines.

Intel Macs are not supported in this build.

### Skill

```bash
npx skills add kl7sn/kilo -g
```

### Limits

- No Apple notarization
- No Intel / universal binary
- Agent sessions need Orca on the machine
