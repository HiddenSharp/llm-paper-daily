# paper-subscribe onboarding

1. Copy `templates/config.example.json` to `~/.paper-subscribe/config.json`
2. Fill in:
   - `feed_url`
   - `timezone`
   - `schedule`
   - `filters`
   - `delivery.channel` (keep `stdout`)
3. Run:

```bash
bash skill/paper-subscribe/scripts/install-cron.sh --config ~/.paper-subscribe/config.json
```

4. Test manually:

```bash
node skill/paper-subscribe/scripts/prepare-digest.js --config ~/.paper-subscribe/config.json > /tmp/digest.json
node skill/paper-subscribe/scripts/deliver.js --config ~/.paper-subscribe/config.json --input /tmp/digest.json
```
