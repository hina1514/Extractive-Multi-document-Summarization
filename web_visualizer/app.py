import os
import re
import sys
import unicodedata
from pathlib import Path

from flask import Flask, jsonify, render_template, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from methods.main_method.Kmeans_CentroidBase_MMR_SentencePosition import Summarizer
from methods.maximal_marginal_relevance.mmr_summarizer import MMR
from utils.sentence import Sentence

try:
    from underthesea import sent_tokenize, word_tokenize
except Exception:
    sent_tokenize = None
    word_tokenize = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


app = Flask(__name__)

PUNCTUATION = {
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    "(",
    ")",
    "`",
    "_",
    "--",
    "``",
    "''",
    "'s",
}


def split_sentences(text):
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").strip()
    if not text:
        return []

    if sent_tokenize:
        try:
            return [sentence.strip() for sentence in sent_tokenize(text) if sentence.strip()]
        except Exception:
            pass

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def tokenize_sentence(sentence):
    sentence = unicodedata.normalize("NFC", sentence).lower()
    if word_tokenize:
        try:
            tokenized = word_tokenize(sentence, format="text")
            tokens = tokenized.split() if isinstance(tokenized, str) else tokenized
        except Exception:
            tokens = re.findall(r"\w+", sentence, flags=re.UNICODE)
    else:
        tokens = re.findall(r"\w+", sentence, flags=re.UNICODE)

    return [
        token
        for token in tokens
        if token.strip() and token not in PUNCTUATION and "&" not in token
    ]


def read_text_file(file_storage):
    data = file_storage.read()
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def read_docx_file(file_storage):
    if Document is None:
        raise ValueError("Chưa cài python-docx để đọc file .docx.")
    document = Document(file_storage.stream)
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def read_pdf_file(file_storage):
    if PdfReader is None:
        raise ValueError("Chưa cài pypdf để đọc file .pdf.")
    reader = PdfReader(file_storage.stream)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def read_uploaded_file(file_storage):
    filename = file_storage.filename or "uploaded"
    suffix = Path(filename).suffix.lower()

    if suffix == ".txt":
        return read_text_file(file_storage)
    if suffix == ".docx":
        return read_docx_file(file_storage)
    if suffix == ".pdf":
        return read_pdf_file(file_storage)
    raise ValueError(f"Không hỗ trợ định dạng {suffix or '(không có đuôi file)'}." )


def clean_document_text(text):
    text = (text or "").strip()
    match = re.search(r"\bContent\s*:", text, flags=re.IGNORECASE)
    if match:
        return text[match.end() :].strip()
    return text


def build_documents(texts, files):
    documents = []
    for index, text in enumerate(texts, start=1):
        text = clean_document_text(text)
        if text:
            documents.append(
                {
                    "name": f"Văn bản nhập {index}",
                    "source": "manual",
                    "text": text,
                }
            )

    for file_storage in files:
        if not file_storage or not file_storage.filename:
            continue
        text = clean_document_text(read_uploaded_file(file_storage))
        if text:
            documents.append(
                {
                    "name": file_storage.filename,
                    "source": "file",
                    "text": text,
                }
            )

    return documents


def preprocess_documents(documents):
    sentence_objects = []
    sentence_records = []
    last_indexs = []

    for doc_index, document in enumerate(documents):
        last_indexs.append(len(sentence_objects))
        kept = 0

        for sentence in split_sentences(document["text"]):
            tokens = tokenize_sentence(sentence)
            if len(tokens) <= 4:
                continue

            sentence_object = Sentence(document["name"], tokens, sentence)
            sentence_id = f"d{doc_index + 1}s{kept + 1}"

            sentence_objects.append(sentence_object)
            sentence_records.append(
                {
                    "id": sentence_id,
                    "docIndex": doc_index,
                    "docName": document["name"],
                    "position": kept,
                    "globalPosition": len(sentence_records),
                    "text": sentence,
                    "tokens": tokens,
                    "tokenCount": len(tokens),
                    "processed": " ".join(tokens),
                }
            )
            kept += 1

    return sentence_objects, sentence_records, last_indexs


def choose_cluster_count(sentence_count):
    if sentence_count < 20:
        return 3
    if sentence_count < 50:
        return 5
    if sentence_count < 100:
        return 8
    return 10


def top_terms_from_existing_mmr(sentence_objects, limit=24):
    terms = []
    for score in sorted(MMR.TF_IDF(sentence_objects).keys(), reverse=True):
        for word in MMR.TF_IDF(sentence_objects)[score]:
            terms.append({"term": word, "weight": float(score)})
            if len(terms) == limit:
                return terms
    return terms


def index_mmr_summaries(new_sents, mmr_summaries):
    indexes = []
    used = set()
    for summary_sentence in mmr_summaries:
        for index, sentence in enumerate(new_sents):
            if index in used:
                continue
            if sentence == summary_sentence:
                indexes.append(index)
                used.add(index)
                break
    return indexes


def summarize(documents, requested_summary_length):
    sentence_objects, sentence_records, last_indexs = preprocess_documents(documents)
    if len(sentence_objects) < 5:
        raise ValueError("Pipeline gốc cần ít nhất 5 câu hợp lệ để chạy KMeans/Centroid/MMR.")

    text_sents = [sentence.getProcessedWords() for sentence in sentence_objects]
    org_sents = [sentence.getOGwords() for sentence in sentence_objects]
    sentence_count = len(sentence_objects)

    n_clusters = min(choose_cluster_count(sentence_count), sentence_count)
    summary_length = min(max(1, requested_summary_length), n_clusters)

    summarizer = Summarizer(n_clusters=n_clusters, len_summary=summary_length)

    new_sents, object_sents = summarizer.kmean_summarizer(
        sentence_objects,
        text_sents,
        org_sents,
        last_indexs,
        n_clusters,
    )

    object_to_original = {id(sentence): index for index, sentence in enumerate(sentence_objects)}
    candidate_to_original = [object_to_original[id(sentence)] for sentence in object_sents]
    raw_sentences = [sentence.getOGwords() for sentence in object_sents]

    len_centroid = min(20, len(new_sents))
    index_sents = summarizer.centroid_summarizer(raw_sentences, new_sents, len_centroid)
    if not index_sents:
        index_sents = list(range(len(object_sents)))

    mmr_summaries = summarizer.mmr_summarizer(
        object_sents,
        index_sents,
        mode="web",
        length_sentence=summary_length,
    )
    mmr_candidate_indexes = index_mmr_summaries(new_sents, mmr_summaries)

    final_candidate_indexes = summarizer.add_position(
        new_sents,
        mmr_summaries,
        summary_length,
        index_sents,
        n_clusters,
    )
    final_candidate_indexes = [
        index for index in final_candidate_indexes if 0 <= index < len(candidate_to_original)
    ]
    selected_original_indexes = [
        candidate_to_original[index] for index in final_candidate_indexes
    ]
    selected_order = {
        original_index: order
        for order, original_index in enumerate(selected_original_indexes, start=1)
    }

    for sentence_index, record in enumerate(sentence_records):
        record["cluster"] = None
        record["selected"] = sentence_index in selected_order
        record["selectedOrder"] = selected_order.get(sentence_index)
        record["mmrScore"] = None

    clusters = []
    for candidate_index, original_index in enumerate(candidate_to_original):
        sentence_records[original_index]["cluster"] = candidate_index + 1
        clusters.append(
            {
                "cluster": candidate_index + 1,
                "sentenceIndex": original_index,
                "sentenceId": sentence_records[original_index]["id"],
                "size": None,
                "score": None,
                "avgPosition": float(sentence_records[original_index]["globalPosition"]),
                "members": [sentence_records[original_index]["id"]],
                "selected": candidate_index in final_candidate_indexes,
                "selectedOrder": selected_order.get(original_index),
                "centroidSelected": candidate_index in index_sents,
                "mmrSelected": candidate_index in mmr_candidate_indexes,
            }
        )

    mmr_steps = []
    for step_order, candidate_index in enumerate(mmr_candidate_indexes, start=1):
        if candidate_index >= len(candidate_to_original):
            continue
        original_index = candidate_to_original[candidate_index]
        mmr_steps.append(
            {
                "sentenceIndex": original_index,
                "candidateIndex": candidate_index,
                "order": step_order,
                "relevance": None,
                "redundancy": None,
                "mmrScore": None,
            }
        )

    summary_sentences = []
    for display_index, candidate_index in enumerate(final_candidate_indexes, start=1):
        original_index = candidate_to_original[candidate_index]
        summary_sentences.append(
            {
                "id": sentence_records[original_index]["id"],
                "docName": sentence_records[original_index]["docName"],
                "text": sentence_records[original_index]["text"],
                "order": display_index,
                "displayOrder": display_index,
            }
        )

    document_views = []
    for doc_index, document in enumerate(documents):
        document_sentences = [
            sentence for sentence in sentence_records if sentence["docIndex"] == doc_index
        ]
        document_views.append(
            {
                "name": document["name"],
                "source": document["source"],
                "sentenceCount": len(document_sentences),
                "sentences": document_sentences,
            }
        )

    vocabulary = {token for sentence in text_sents for token in sentence}

    return {
        "documents": document_views,
        "stats": {
            "documentCount": len(documents),
            "sentenceCount": sentence_count,
            "summaryLength": len(summary_sentences),
            "clusterCount": n_clusters,
            "candidateCount": len(candidate_to_original),
            "vocabularySize": len(vocabulary),
        },
        "steps": {
            "preprocess": {
                "sentences": sentence_records,
                "topTerms": top_terms_from_existing_mmr(sentence_objects),
            },
            "clusters": clusters,
            "mmr": mmr_steps,
        },
        "summary": summary_sentences,
        "pipeline": "methods/main_method/Kmeans_CentroidBase_MMR_SentencePosition.py",
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    try:
        texts = request.form.getlist("texts")
        files = request.files.getlist("files")
        summary_length = int(request.form.get("summaryLength", "6"))
        documents = build_documents(texts, files)

        if not documents:
            return jsonify({"error": "Hãy nhập văn bản hoặc chọn ít nhất một file."}), 400

        result = summarize(documents, summary_length)
        return jsonify(result)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": f"Lỗi khi xử lý: {error}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("WEB_VIS_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)
