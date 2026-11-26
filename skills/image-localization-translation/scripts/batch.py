"""Render an ordered manifest and perform per-block OCR. Model and visual reviews run in Codex."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from render import render

MARKETS = {"VN": ("VN_越南语", "vie"), "PH": ("PH_菲律宾英语", "eng")}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def run(manifest, output, tessdata, markets=("VN", "PH")):
    jobs = read(manifest)
    if not jobs:
        raise ValueError("Empty batch")
    names = set()
    for job in jobs:
        source = Path(job["source"]).resolve(strict=True)
        name = job.get("name", source.stem)
        if Path(name).name != name or not name.strip() or name.casefold() in names:
            raise ValueError(f"Choose a unique output stem: {name}")
        names.add(name.casefold())
        if set(job["plans"]) != set(markets):
            raise ValueError(f"{name}: expected {list(markets)}, got {list(job['plans'])}")
        for plan in job["plans"].values():
            if Path(read(plan)["source"]).resolve(strict=True) != source:
                raise ValueError(f"Plan points to different source: {plan}")
    if output.exists():
        raise ValueError(f"Choose an unused output root: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name+"-work-", dir=output.parent))
    qa = stage / "QA_审核记录"
    qa.mkdir()
    summary = []
    for index, job in enumerate(jobs, 1):
        name = job.get("name", Path(job["source"]).stem)
        for market, plan_path in job["plans"].items():
            folder, language = MARKETS[market]
            dest = stage / folder / (name + ".png")
            used = render(read(plan_path), dest)
            process = subprocess.run(["node", str(Path(__file__).with_name("ocr.cjs")),
                                      str(dest), language, str(tessdata), plan_path],
                                     capture_output=True, encoding="utf-8")
            if process.returncode not in (0, 2):
                raise RuntimeError(f"OCR failed for {dest}: {process.stderr}")
            result = json.loads(process.stdout)
            result["file"] = str(dest.relative_to(stage))
            summary.append(dict(index=index, market=market, source=job["source"], rendered=used,
                                ocr=result, status="needs_visual_review" if process.returncode == 0
                                else "needs_ocr_discrepancy_review"))
    (qa / "batch-checks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    os.rename(stage, output)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("manifest", "fresh_output", "local_tessdata"):
        parser.add_argument(key, type=Path)
    parser.add_argument("--markets", nargs="+", choices=MARKETS, default=["VN", "PH"])
    args = parser.parse_args()
    results = run(args.manifest, args.fresh_output, args.local_tessdata, args.markets)
    print(f"{len(results)} rendered. Inspect batch-checks.json and complete visual review.")
