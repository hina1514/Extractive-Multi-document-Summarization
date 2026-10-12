import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "Data" / "ViMs"


def read_text(path):
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def tokenize(text):
    text = unicodedata.normalize("NFC", text).lower()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def ngrams(tokens, n):
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def prf(overlap, candidate_total, reference_total):
    if candidate_total == 0 or reference_total == 0 or overlap == 0:
        return {"p": 0.0, "r": 0.0, "f1": 0.0}

    precision = overlap / candidate_total
    recall = overlap / reference_total
    f1 = 2 * precision * recall / (precision + recall)
    return {"p": precision, "r": recall, "f1": f1}


def rouge_n(candidate_tokens, reference_tokens, n):
    candidate_ngrams = Counter(ngrams(candidate_tokens, n))
    reference_ngrams = Counter(ngrams(reference_tokens, n))
    overlap = sum((candidate_ngrams & reference_ngrams).values())
    return prf(overlap, sum(candidate_ngrams.values()), sum(reference_ngrams.values()))


def lcs_length(left, right):
    if not left or not right:
        return 0

    previous = [0] * (len(right) + 1)
    for left_token in left:
        current = [0]
        for index, right_token in enumerate(right, start=1):
            if left_token == right_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def rouge_l(candidate_tokens, reference_tokens):
    overlap = lcs_length(candidate_tokens, reference_tokens)
    return prf(overlap, len(candidate_tokens), len(reference_tokens))


def score_pair(candidate_text, reference_text):
    candidate_tokens = tokenize(candidate_text)
    reference_tokens = tokenize(reference_text)
    return {
        "rouge-1": rouge_n(candidate_tokens, reference_tokens, 1),
        "rouge-2": rouge_n(candidate_tokens, reference_tokens, 2),
        "rouge-l": rouge_l(candidate_tokens, reference_tokens),
    }


def mean(values):
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def flatten_scores(scores, prefix=""):
    row = {}
    for metric_name, metric_scores in scores.items():
        metric_key = metric_name.replace("-", "_")
        row[f"{prefix}{metric_key}"] = metric_scores["f1"]
    return row


def reference_files(reference_dir):
    return sorted(
        path
        for path in reference_dir.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )


def cluster_name_from_generated(path):
    return path.stem


def evaluate(generated_dir, reference_dir):
    detail_rows = []
    cluster_rows = []
    missing_rows = []

    generated_files = sorted(
        path
        for path in generated_dir.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )

    for generated_file in generated_files:
        cluster_name = cluster_name_from_generated(generated_file)
        cluster_reference_dir = reference_dir / cluster_name

        if not cluster_reference_dir.is_dir():
            missing_rows.append(
                {
                    "cluster": cluster_name,
                    "generated_file": str(generated_file),
                    "problem": "missing_reference_folder",
                }
            )
            continue

        refs = reference_files(cluster_reference_dir)
        if not refs:
            missing_rows.append(
                {
                    "cluster": cluster_name,
                    "generated_file": str(generated_file),
                    "problem": "missing_reference_files",
                }
            )
            continue

        candidate_text = read_text(generated_file)
        cluster_scores = []

        for reference_file in refs:
            scores = score_pair(candidate_text, read_text(reference_file))
            cluster_scores.append(scores)

            detail_rows.append(
                {
                    "cluster": cluster_name,
                    "generated_file": str(generated_file),
                    "reference_file": str(reference_file),
                    **flatten_scores(scores),
                }
            )

        aggregate = {
            "cluster": cluster_name,
            "generated_file": str(generated_file),
            "reference_count": len(refs),
        }

        for metric in ("rouge-1", "rouge-2", "rouge-l"):
            metric_key = metric.replace("-", "_")
            aggregate[metric_key] = mean(
                scores[metric]["f1"] for scores in cluster_scores
            )

        cluster_rows.append(aggregate)

    return detail_rows, cluster_rows, missing_rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(cluster_rows, detail_rows, missing_rows):
    summary = {
        "clusters_scored": len(cluster_rows),
        "reference_comparisons": len(detail_rows),
        "missing": missing_rows,
        "macro_average": {},
    }

    for metric in ("rouge_1", "rouge_2", "rouge_l"):
        summary["macro_average"][metric] = mean(row[metric] for row in cluster_rows)

    return summary


def print_summary(summary):
    print(f"Clusters scored: {summary['clusters_scored']}")
    print(f"Reference comparisons: {summary['reference_comparisons']}")
    if summary["missing"]:
        print(f"Missing clusters/files: {len(summary['missing'])}")

    print("\nMacro average over clusters")
    for metric in ("rouge_1", "rouge_2", "rouge_l"):
        print(f"{metric}: {summary['macro_average'][metric]:.4f}")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate generated ViMs summaries against the two human gold summaries "
            "with ROUGE-1, ROUGE-2, and ROUGE-L."
        )
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=DEFAULT_DATA_DIR / "GeneratedSummary",
        help="Folder containing generated files such as Cluster_001.me.",
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=DEFAULT_DATA_DIR / "summary",
        help="Folder containing gold folders such as Cluster_001/0.gold.txt.",
    )
    parser.add_argument(
        "--detail-csv",
        type=Path,
        default=Path("rouge_detail_scores.csv"),
        help="CSV output for each generated summary versus each gold summary.",
    )
    parser.add_argument(
        "--cluster-csv",
        type=Path,
        default=Path("rouge_cluster_scores.csv"),
        help="CSV output aggregated by cluster.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("rouge_summary.json"),
        help="JSON output containing corpus-level macro averages.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    detail_rows, cluster_rows, missing_rows = evaluate(
        args.generated_dir,
        args.reference_dir,
    )

    write_csv(args.detail_csv, detail_rows)
    write_csv(args.cluster_csv, cluster_rows)

    summary = build_summary(cluster_rows, detail_rows, missing_rows)
    args.summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print_summary(summary)
    print(f"\nWrote: {args.detail_csv}")
    print(f"Wrote: {args.cluster_csv}")
    print(f"Wrote: {args.summary_json}")


if __name__ == "__main__":
    main()
