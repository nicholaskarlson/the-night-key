# Bereavement Textgame — Day 1

This is the canonical “Day 1” story source for the project.

- Source: `stories/bereavement_day1/scenes.yaml`
- Pack output (via `make packs`): `dist/packs/bereavement_day1.pack.zip`

## Build the pack

From the repo root:

```bash
make packs
```

## Verify and play

```bash
btg verify-pack dist/packs/bereavement_day1.pack.zip
btg play --pack dist/packs/bereavement_day1.pack.zip
```

## Authoring notes

This story uses five “memory thread” flags that unlock conditional choices:

- `called_mom`
- `asked_for_help`
- `used_humor`
- `touched_shovel`
- `listened_voicemail`

You can extend the story by adding new scenes and linking them with `goto`.
Keep running:

```bash
btg lint --strict --scenes stories/bereavement_day1/scenes.yaml
```
