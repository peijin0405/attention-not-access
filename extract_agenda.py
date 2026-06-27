#!/usr/bin/env python3
"""
Extract structured agenda records from Blockchain Futurist Conference screenshots.

The pipeline intentionally uses only Python's standard library plus the local
Tesseract CLI, because this environment does not include OCR/dataframe packages.
It saves raw OCR per image, then parses agenda cards conservatively:
session title -> time range -> optional speaker line(s) -> stage/venue line.
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
PIC_DIR = ROOT / "pic"
OUTPUT_DIR = ROOT / "output"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

EVENT_NAME = "Blockchain Futurist Conference"

TIME_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}\s*(?:am|pm))\s*[-–—]\s*(?P<end>\d{1,2}:\d{2}\s*(?:am|pm))",
    re.IGNORECASE,
)
SPEAKER_RE = re.compile(r"([^(),]+?)\s*\(([^()]+)\)")
VENUE_PREFIX_RE = re.compile(r"^[©@o0]\s+", re.IGNORECASE)

TOPIC_KEYWORDS = [
    ("AI x Crypto", [" ai ", "artificial intelligence", "agent", "machine learning"]),
    ("DeFi", ["defi", "staking", "yield", "liquidity", "dex", "lending"]),
    ("RWA / Tokenization", ["rwa", "tokeniz", "real estate", "property", "diamond", "mineral"]),
    ("Stablecoins / Payments", ["stablecoin", "payment", "fintech", "merchant", "banking"]),
    ("DePIN", ["depin", "physical infrastructure", "wireless", "sensor"]),
    ("Layer 1 / Layer 2", ["layer 1", "layer 2", "l1", "l2", "rollup", "ethereum", "bitcoin layer"]),
    ("Infrastructure", ["infrastructure", "protocol", "developer", "web3", "wallet", "node", "quantum"]),
    ("Security / Privacy", ["security", "privacy", "custody", "threat", "risk", "hack", "audit"]),
    ("Regulation / Policy", ["regulation", "policy", "government", "legal", "compliance", "house of representatives"]),
    ("Venture Capital / Fundraising", ["venture", "fundraising", "funding", "investor", "capital", "vc"]),
    ("Gaming / Metaverse", ["gaming", "game", "metaverse", "tcg"]),
    ("NFT / Creator Economy", ["nft", "creator", "collectible", "artist"]),
    ("Bitcoin", ["bitcoin", "btc"]),
    ("Institutional Crypto", ["institutional", "etf", "treasury", "asset manager"]),
    ("Identity / Reputation", ["identity", "reputation", "did", "credential"]),
    ("Consumer Crypto", ["consumer", "travel", "social", "retail", "loyalty"]),
]

FIELDNAMES = [
    "source_file",
    "event_name",
    "date",
    "start_time",
    "end_time",
    "stage_or_venue",
    "session_title",
    "session_type",
    "session_description",
    "speaker_name",
    "speaker_title",
    "speaker_company",
    "topic_category",
    "raw_text",
    "confidence_level",
    "notes",
]


@dataclass
class OcrResult:
    source_file: str
    raw_text: str
    avg_confidence: float
    error: str = ""


@dataclass
class SessionRow:
    source_file: str
    event_name: str
    date: str
    start_time: str
    end_time: str
    stage_or_venue: str
    session_title: str
    session_type: str
    session_description: str
    speaker_name: str
    speaker_title: str
    speaker_company: str
    topic_category: str
    raw_text: str
    confidence_level: str
    notes: str


def list_images(pic_dir: Path) -> list[Path]:
    if not pic_dir.exists():
        return []
    return sorted(
        p for p in pic_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def run_tesseract(image_path: Path) -> OcrResult:
    """Return plain text plus mean word confidence from Tesseract TSV output."""
    try:
        text_proc = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "eng", "--psm", "6"],
            check=False,
            capture_output=True,
            text=True,
        )
        tsv_proc = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "eng", "--psm", "6", "tsv"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return OcrResult(image_path.name, "", 0.0, "tesseract executable not found")
    except Exception as exc:  # Keep the batch moving if one file is problematic.
        return OcrResult(image_path.name, "", 0.0, f"OCR exception: {exc}")

    errors = []
    if text_proc.returncode != 0:
        errors.append(text_proc.stderr.strip())
    if tsv_proc.returncode != 0:
        errors.append(tsv_proc.stderr.strip())

    confidences: list[float] = []
    lines = tsv_proc.stdout.splitlines()
    if lines:
        reader = csv.DictReader(lines, delimiter="\t")
        for row in reader:
            word = (row.get("text") or "").strip()
            conf = row.get("conf") or "-1"
            if not word:
                continue
            try:
                value = float(conf)
            except ValueError:
                continue
            if value >= 0:
                confidences.append(value)

    avg_conf = statistics.mean(confidences) if confidences else 0.0
    return OcrResult(image_path.name, text_proc.stdout.strip(), avg_conf, " | ".join(errors))


def clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    line = line.replace("—", "-").replace("–", "-")
    return line


def useful_lines(raw_text: str) -> list[str]:
    skip_patterns = [
        re.compile(r"^<\s*Agenda", re.I),
        re.compile(r"Filters|Search", re.I),
        re.compile(r"^Eoow|^Nov\s*\[|^I=$|^\W{1,4}$", re.I),
    ]
    out = []
    for line in raw_text.splitlines():
        line = clean_line(line)
        if not line:
            continue
        if any(p.search(line) for p in skip_patterns):
            continue
        out.append(line)
    return out


def normalize_time(text: str) -> tuple[str, str] | None:
    match = TIME_RE.search(text)
    if not match:
        return None
    return (clean_line(match.group("start").lower()), clean_line(match.group("end").lower()))


def is_venue_line(line: str) -> bool:
    lower = line.lower()
    return bool(VENUE_PREFIX_RE.search(line)) or "stage" in lower or "bootcamp" in lower


def normalize_venue(line: str) -> str:
    line = re.sub(r"^[©@o0]\s*", "", line).strip()
    line = line.replace("Stagee", "Stage e")
    line = re.sub(r"\s+(?:[•e])\s+", " | ", line)
    line = re.sub(r"\bStag\b", "Stage", line)
    line = line.replace("Argentum Al Stage", "Argentum AI Stage")
    line = line.replace("Arg | ntum Al Stage | @ Entic | ETHWom | n", "Argentum AI Stage @ Entice")
    line = line.replace("Arg | ntum Al Stage | @ Entic | Al", "Argentum AI Stage @ Entice")
    line = line.replace("Arg | ntum Al Stage | @ Entic | Ev | nts", "Argentum AI Stage @ Entice")
    line = line.replace("Futurist | Ev | nts", "Futurist")
    line = line.replace("Main Stage | Ev | nts", "Main Stage")
    line = line.replace("Rooftop Stage | Ev | nts", "Rooftop Stage")
    line = line.replace("Outdoor Cabana | Ev | nts", "Outdoor Cabana")
    line = line.replace(" | Al", " | AI")
    parts = [p.strip(" .") for p in line.split("|") if p.strip(" .")]
    if len(parts) >= 2 and parts[0].lower() == parts[1].lower():
        return parts[0]
    return " | ".join(parts) if parts else line


def extract_date(raw_text: str) -> str:
    # The screenshots often show an abbreviated month tab without a full date.
    match = re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2}\b", raw_text, re.I)
    return match.group(0) if match else ""


def infer_session_type(title: str) -> str:
    lower = title.lower()
    if lower.startswith("panel:") or lower.startswith("panel "):
        return "Panel"
    if "fireside" in lower:
        return "Fireside Chat"
    if "keynote" in lower:
        return "Keynote"
    if "workshop" in lower or "bootcamp" in lower:
        return "Workshop"
    if lower.startswith("announcement"):
        return "Announcement"
    if lower.startswith("presentation") or "presented by" in lower:
        return "Presentation"
    if "opening" in lower or "welcoming" in lower:
        return "Opening / Welcome"
    return ""


def clean_title(title: str) -> str:
    title = clean_line(title)
    title = re.sub(
        r"^\d{1,2}:\d{2}\s*(?:\d+\s*)?[A-Z\\/\s]*\b(?:all|wl)\b\s*>?\s*[€E]?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"^\d{1,2}:\d{2}[A-Z\\/\s]*>\s*[€E]?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^\d+\s+(?=[A-Z])", "", title)
    title = re.sub(r"\s+[7FAIt]{1,3}$", "", title).strip()
    title = re.sub(r"\bAl\b", "AI", title)
    return title


def categorize(title: str, description: str) -> str:
    padded = f" {title} {description} ".lower()
    for category, keywords in TOPIC_KEYWORDS:
        if any(keyword in padded for keyword in keywords):
            return category
    return "Other"


def extract_speakers(text: str) -> list[tuple[str, str]]:
    speakers = []
    for name, company in SPEAKER_RE.findall(text):
        clean_name = clean_line(name).strip(" ,")
        clean_company = clean_line(company).strip(" ,")
        if clean_company and not re.search(r"[A-Za-z0-9]", clean_company):
            clean_company = ""
        if clean_name:
            speakers.append((clean_name, clean_company))
    return speakers


def fallback_speaker_name(text: str) -> str:
    if not text or "(" in text or ")" in text:
        return ""
    if len(text.split()) > 5:
        return ""
    if any(token.lower() in text.lower() for token in ["stage", "doors", "open", "presented"]):
        return ""
    return text.strip(" ,")


def parse_sessions(ocr: OcrResult) -> list[SessionRow]:
    lines = useful_lines(ocr.raw_text)
    date = extract_date(ocr.raw_text)
    rows: list[SessionRow] = []
    i = 0

    while i < len(lines):
        time_info = normalize_time(lines[i])
        if not time_info:
            i += 1
            continue

        title_lines: list[str] = []
        j = i - 1
        while j >= 0 and not normalize_time(lines[j]) and not is_venue_line(lines[j]):
            candidate = lines[j]
            if not candidate.startswith("[") and not candidate.startswith("HH"):
                title_lines.insert(0, candidate)
            j -= 1
            if len(" ".join(title_lines)) > 160:
                break

        title = clean_title(" ".join(title_lines))
        start_time, end_time = time_info
        speaker_lines: list[str] = []
        venue = ""
        k = i + 1
        while k < len(lines):
            if normalize_time(lines[k]):
                break
            if is_venue_line(lines[k]):
                venue = normalize_venue(lines[k])
                k += 1
                break
            speaker_lines.append(lines[k])
            k += 1

        speaker_blob = " ".join(speaker_lines)
        speakers = extract_speakers(speaker_blob)
        if not speakers:
            fallback_name = fallback_speaker_name(speaker_blob)
            speakers = [(fallback_name, "")] if fallback_name else [("", "")]

        notes = []
        if not title:
            notes.append("Missing session title from OCR context.")
        if not venue:
            notes.append("Missing or uncertain stage/venue.")
        if not date:
            notes.append("No full date visible in OCR.")
        title_has_ocr_artifacts = bool(title and (re.search(r"[><]{1,}", title) or re.search(r"^\W", title)))
        if title_has_ocr_artifacts:
            notes.append("Session title contains likely OCR artifacts.")
        if speaker_blob and not extract_speakers(speaker_blob):
            notes.append("Speaker/company pattern not confidently parsed.")
        if ocr.avg_confidence < 70:
            notes.append(f"Low average OCR confidence: {ocr.avg_confidence:.1f}.")
        if ocr.error:
            notes.append(f"OCR warning: {ocr.error}")

        critical_missing = not title or not start_time or not end_time or not venue or title_has_ocr_artifacts
        confidence = "low" if critical_missing or ocr.avg_confidence < 65 else "medium"
        if confidence != "low" and title and venue and speakers and ocr.avg_confidence >= 82:
            confidence = "high"

        for speaker_name, speaker_company in speakers:
            if not speaker_name:
                notes_for_row = notes + ["No speaker name visible or confidently extracted."]
            else:
                notes_for_row = notes.copy()
            if speaker_name and not speaker_company:
                notes_for_row.append("Speaker company not visible or confidently extracted.")

            rows.append(
                SessionRow(
                    source_file=ocr.source_file,
                    event_name=EVENT_NAME,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    stage_or_venue=venue,
                    session_title=title,
                    session_type=infer_session_type(title),
                    session_description="",
                    speaker_name=speaker_name,
                    speaker_title="",
                    speaker_company=speaker_company,
                    topic_category=categorize(title, ""),
                    raw_text=ocr.raw_text,
                    confidence_level=confidence,
                    notes=" ".join(dict.fromkeys(notes_for_row)),
                )
            )

        i = max(k, i + 1)

    if not rows and ocr.raw_text:
        rows.append(
            SessionRow(
                source_file=ocr.source_file,
                event_name=EVENT_NAME,
                date=date,
                start_time="",
                end_time="",
                stage_or_venue="",
                session_title="",
                session_type="",
                session_description="",
                speaker_name="",
                speaker_title="",
                speaker_company="",
                topic_category="Other",
                raw_text=ocr.raw_text,
                confidence_level="low",
                notes="OCR text present, but no agenda session time blocks were parsed.",
            )
        )
    return rows


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_by(rows: list[SessionRow], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = getattr(row, field) or "(blank)"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def make_quality_report(images: list[Path], ocr_results: list[OcrResult], rows: list[SessionRow]) -> str:
    missing_counts = {field: 0 for field in FIELDNAMES}
    for row in rows:
        data = asdict(row)
        for field, value in data.items():
            if value == "":
                missing_counts[field] += 1

    low_rows = [row for row in rows if row.confidence_level == "low"]
    speakers_extracted = sum(1 for row in rows if row.speaker_name)
    ocr_warnings = [ocr for ocr in ocr_results if ocr.error]

    lines = [
        "# Data Quality Report",
        "",
        f"- Images processed: {len(images)}",
        f"- Sessions extracted: {len({(r.source_file, r.start_time, r.end_time, r.session_title) for r in rows if r.session_title})}",
        f"- Speaker rows extracted: {speakers_extracted}",
        f"- Structured rows written: {len(rows)}",
        "",
        "## Missing Field Counts",
        "",
    ]
    for field, count in missing_counts.items():
        lines.append(f"- {field}: {count}")

    lines.extend(["", "## Low-Confidence Rows", ""])
    if low_rows:
        for idx, row in enumerate(low_rows[:50], start=1):
            lines.append(
                f"- {idx}. {row.source_file} | {row.start_time}-{row.end_time} | "
                f"{row.session_title or '(missing title)'} | notes: {row.notes}"
            )
        if len(low_rows) > 50:
            lines.append(f"- ... {len(low_rows) - 50} additional low-confidence rows omitted.")
    else:
        lines.append("- None")

    lines.extend(["", "## Common OCR Issues", ""])
    common_issues = [
        "Decorative mobile-app icons are sometimes recognized as stray characters such as HH, FA, or punctuation.",
        "Venue bullets can be recognized as ©, e, @, or o, so venue parsing normalizes these but may still be imperfect.",
        "Speaker titles are generally not visible in the agenda list screenshots and are left blank.",
        "Full agenda dates are often not visible; partial month-tab text is not treated as a reliable date.",
        "Company names are extracted only when OCR preserves the visible parenthesized company pattern.",
    ]
    for issue in common_issues:
        lines.append(f"- {issue}")
    if ocr_warnings:
        lines.append("- Tesseract emitted warnings for some files; see raw OCR CSV error column.")

    lines.extend(["", "## Recommendations For Manual Review", ""])
    recommendations = [
        "Review every low-confidence row and every row with blank title, time, venue, or speaker fields.",
        "Validate multi-speaker panels against the screenshots, especially where names or companies contain OCR punctuation errors.",
        "Fill speaker titles from a speaker-detail source if required; they are not reliably present in these agenda-list screenshots.",
        "Confirm the conference date from the app day selector or an external official agenda before using the date field analytically.",
    ]
    for recommendation in recommendations:
        lines.append(f"- {recommendation}")

    return "\n".join(lines) + "\n"


def print_table(rows: list[SessionRow], limit: int = 20) -> None:
    cols = ["source_file", "start_time", "end_time", "stage_or_venue", "session_title", "speaker_name", "speaker_company", "topic_category", "confidence_level"]
    print(f"\nFirst {min(limit, len(rows))} structured rows:")
    print("\t".join(cols))
    for row in rows[:limit]:
        data = asdict(row)
        print("\t".join(str(data[c]).replace("\n", " ")[:90] for c in cols))


def print_counts(title: str, counts: dict[str, int]) -> None:
    print(f"\n{title}:")
    for key, value in counts.items():
        print(f"{key}: {value}")


def main() -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    images = list_images(PIC_DIR)
    if not images:
        print(f"No supported images found in {PIC_DIR}", file=sys.stderr)
        return 1

    ocr_results = [run_tesseract(image) for image in images]
    rows: list[SessionRow] = []
    for ocr in ocr_results:
        rows.extend(parse_sessions(ocr))

    raw_ocr_rows = [
        {
            "source_file": ocr.source_file,
            "raw_text": ocr.raw_text,
            "avg_ocr_confidence": f"{ocr.avg_confidence:.2f}",
            "error": ocr.error,
        }
        for ocr in ocr_results
    ]
    write_csv(
        OUTPUT_DIR / "raw_ocr_results.csv",
        raw_ocr_rows,
        ["source_file", "raw_text", "avg_ocr_confidence", "error"],
    )

    structured_dicts = [asdict(row) for row in rows]
    write_csv(OUTPUT_DIR / "structured_sessions.csv", structured_dicts, FIELDNAMES)
    with (OUTPUT_DIR / "structured_sessions.json").open("w", encoding="utf-8") as fh:
        json.dump(structured_dicts, fh, indent=2, ensure_ascii=False)

    report = make_quality_report(images, ocr_results, rows)
    (OUTPUT_DIR / "data_quality_report.md").write_text(report, encoding="utf-8")

    print(f"Images processed: {len(images)}")
    print(f"Rows written: {len(rows)}")
    print_table(rows, 20)
    print_counts("Counts by topic_category", count_by(rows, "topic_category"))
    print_counts("Counts by stage_or_venue", count_by(rows, "stage_or_venue"))

    print("\nRows with low confidence or missing critical fields:")
    critical = [
        row
        for row in rows
        if row.confidence_level == "low"
        or not row.session_title
        or not row.start_time
        or not row.end_time
        or not row.stage_or_venue
    ]
    for row in critical[:50]:
        print(
            f"{row.source_file}\t{row.start_time}-{row.end_time}\t"
            f"{row.stage_or_venue or '(blank venue)'}\t{row.session_title or '(blank title)'}\t{row.notes}"
        )
    if len(critical) > 50:
        print(f"... {len(critical) - 50} additional rows omitted")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
