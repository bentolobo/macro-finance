# Macro Finance — Living Edition (runnable repo)

Everything here is wired. On a machine with internet and a free FRED key, one
command produces the real book with today's data.

## 20-minute first run

**1 · Install Quarto** — <https://quarto.org/docs/get-started/> (one installer,
Mac/Windows/Linux). Verify: `quarto --version` → 1.6 or later.

**2 · Python deps**

```bash
cd macro-finance
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3 · FRED key** — free, 30 seconds, no approval wait:
<https://fred.stlouisfed.org/docs/api/api_key.html>

```bash
cp .env.example .env     # then paste the key after FRED_API_KEY=
```

**4 · Check before you build**

```bash
make doctor
```

This is the command that answers your question. It fetches every series the book
uses and prints a tier report: `live`, `cache`, or `curated`. If it says
**live: 4**, your next render is the real thing.

**5 · Build**

```bash
make html        # → _output/index.html, open it
make pdf         # → _output/Macro-Finance.pdf
make preview     # live reload while you edit
```

## What "live" looks like

Before the render, `chapters/01-introduction.qmd` contains:

```
The latest observation is **`{python} f"{usd.iloc[-1]:,.1f}"`**, dated
`{python} usd.index[-1].strftime('%d %B %Y')`.
```

After it, the page reads a real number and a real date, and the dollar-index
chart ends at the most recent business day. Re-run tomorrow and both move.
No editing.

## If a figure says "ILLUSTRATIVE SHAPE"

That series could not be reached. Causes, in order of likelihood: no `.env` key
(FRED only), campus firewall blocking outbound HTTPS, or the agency is down.
`make doctor` names the failing endpoint and the exact error. The book still
renders — that is the design — but the watermark tells the reader the figure is
not real.

## Publishing

```bash
make deploy      # quarto publish gh-pages
```

Then push to GitHub and add `FRED_API_KEY` under
Settings → Secrets and variables → Actions. `.github/workflows/render.yml`
re-fetches data and headlines, re-renders and republishes every day at 11:17 UTC.

## What is and isn't in here

- Chapters 1 and 2 are **short live-data skeletons**, not the finished text.
  They exist to prove the pipeline end to end. The full prose lives in the Word
  files; it gets pasted into these `.qmd` files around the existing code chunks.
- `cache/` is git-tracked on purpose: it guarantees the book builds on a student
  laptop with no keys and no network.
- `cache/vintages/` starts recording on your first build. "Then and Now" cannot
  retroactively learn what the dollar index was in October 2026 — the archive has
  to start now, which is why `archive_vintage()` is already called in both chapters.
