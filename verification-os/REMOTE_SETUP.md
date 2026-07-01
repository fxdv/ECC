# Private repo setup

VerificationOS is prepared as a **standalone git repository**. Cloud Agent tokens cannot create GitHub repositories; finish with your account (one command).

## Option A — create + push (recommended)

From this directory, with [GitHub CLI](https://cli.github.com/) logged in as **fxdv**:

```bash
chmod +x scripts/create-and-push-private-repo.sh
./scripts/create-and-push-private-repo.sh fxdv verification-os
```

Custom owner/name:

```bash
./scripts/create-and-push-private-repo.sh YOUR_USER verification-os
```

## Option B — empty repo first, then push

1. Create an empty **private** repo on GitHub: `fxdv/verification-os` (no README/license).
2. Push:

```bash
git remote add origin git@github.com:fxdv/verification-os.git
git push -u origin main
```

HTTPS:

```bash
git remote add origin https://github.com/fxdv/verification-os.git
git push -u origin main
```

## Option C — restore from bundle (another machine)

A git bundle is at `/workspace/verification-os.bundle` on the agent VM:

```bash
git clone verification-os.bundle verification-os
cd verification-os
./scripts/create-and-push-private-repo.sh fxdv verification-os
```

## Verify

```bash
pip install -e ".[dev]"
pytest -q
vos dashboard --port 8080
```
