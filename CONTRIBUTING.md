# Contributing

1. Begin with `python3 tools/continuity.py resume`; do not create a competing active task.
2. Resolve styles by stable style ID, workflow code and canonical IDs—not a similar name.
3. Keep working payload under `workflows/current/`; promote accepted durable material into the target `styles/<style-id>/` directory.
4. Log material decisions/actions/results/errors and long-running process IDs.
5. Checkpoint before/after long work, after material results, before ending a turn and at least every 55 minutes while active.
6. Do not edit imported historical authority/gate files to make history appear cleaner; append a new version/reconciliation record.
7. Large masters belong on Drive with exact ID/hash. Never commit personal reference videos, voice samples, secrets or connector credentials.
8. Add objective tests/gates for behavioral changes.
9. Update the style knowledge index and every required remote record before completion.
10. Run:

```bash
python3 tools/studio.py manifest --write
python3 tools/studio.py validate
python3 tools/continuity.py audit --max-age-minutes 70
python3 -m unittest discover -s tests -v
```

Submodule upgrades require a reviewed pin, license/security review and explicit compatibility note.