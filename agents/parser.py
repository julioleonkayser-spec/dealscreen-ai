"""Agent 1: PDF Parser — extracts text from each page of a PDF."""

import sys
from pathlib import Path


def parse_pdf(file_path: str) -> dict:
    """
    Parse a PDF and return page-by-page text plus full concatenated string.

    Returns:
        {
            "pages": {1: "...", 2: "..."},
            "full_text": "...",
            "page_count": N,
            "error": None or str,
        }
    """
    result = {
        "pages": {},
        "full_text": "",
        "page_count": 0,
        "error": None,
    }

    if not file_path:
        result["error"] = "No file path provided."
        return result

    path = Path(file_path)
    if not path.exists():
        result["error"] = f"File not found: {file_path}"
        return result

    if path.suffix.lower() != ".pdf":
        result["error"] = f"Expected a .pdf file, got: {path.suffix}"
        return result

    try:
        import pdfplumber
    except ImportError:
        result["error"] = "pdfplumber is not installed. Run: pip install pdfplumber"
        return result

    try:
        with pdfplumber.open(str(path)) as pdf:
            result["page_count"] = len(pdf.pages)

            if result["page_count"] == 0:
                result["error"] = "PDF has no pages."
                return result

            text_chunks = []
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as page_err:
                    text = f"[PAGE {i} EXTRACTION ERROR: {page_err}]"

                if not text.strip():
                    text = f"[PAGE {i}: NO EXTRACTABLE TEXT — may be scanned/image-only]"

                result["pages"][i] = text
                text_chunks.append(f"--- PAGE {i} ---\n{text}")

            result["full_text"] = "\n\n".join(text_chunks)

    except Exception as e:
        result["error"] = f"Failed to open PDF: {e}"

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output = parse_pdf(pdf_path)

    if output["error"]:
        print(f"ERROR: {output['error']}")
        sys.exit(1)

    print(f"Pages parsed: {output['page_count']}")
    for page_num, text in output["pages"].items():
        preview = text[:200].replace("\n", " ")
        print(f"\n[Page {page_num}] {preview}...")
