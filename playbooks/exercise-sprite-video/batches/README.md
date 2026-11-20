# Overnight batches

`python3 kit/make_batch.py --out batches/<date>` writes a folder for an image tool to work through unattended:

- `refs-A/` and `refs-B/`: every reference file a request needs, named exactly as the jobs call them.
- `BATCH-A-sprites.md`, `BATCH-B-backgrounds.md`: paste-ready requests. Attach every file in the matching `refs-` folder to ONE message, then paste the text below the line.
- `jobs.json`: the job list (title, attached files, output) without the prompts, for matching results back.

Jobs run in priority order, so if the tool stops part-way the important ones are done. When results come back, send me the whole images (the sheets), and I log each one in `library/` with measurements and grades, pick the best per exercise, and wire the picks.

The prompts come from `prompts/strips.json` and `prompts/backgrounds.json`; edit those, not the batch files, then regenerate.
