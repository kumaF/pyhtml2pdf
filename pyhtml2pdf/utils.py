from pathlib import Path

import pikepdf


def __has_javascript(pdf: pikepdf.Pdf) -> bool:
    root = pdf.Root

    # OpenAction
    if "/OpenAction" in root:
        return True

    # JavaScript name tree
    names = root.get("/Names")
    if names and "/JavaScript" in names:
        return True

    # Page-level actions
    for page in pdf.pages:
        if "/AA" in page.obj:
            return True

    return False


# def __has_launch_action(pdf: pikepdf.Pdf) -> bool:
#     def walk(obj):
#         print(obj)

#         if isinstance(obj, pikepdf.Dictionary):
#             if obj.get("/S") == "/Launch":
#                 return True

#             for _, v in obj.items():
#                 if walk(v):
#                     return True

#         elif isinstance(obj, (list, tuple)):
#             return any(walk(v) for v in obj)

#         return False

#     return walk(pdf.Root)


def __has_embedded_files(pdf: pikepdf.Pdf) -> bool:
    root = pdf.Root
    names = root.get("/Names")
    if not names:
        return False

    ef_tree = names.get("/EmbeddedFiles")
    return ef_tree is not None


def __has_rich_media(pdf: pikepdf.Pdf) -> bool:
    for page in pdf.pages:
        annots = page.obj.get("/Annots", [])
        for annot in annots:
            if annot.get("/Subtype") == "/RichMedia":
                return True
    return False


def __has_xfa(pdf: pikepdf.Pdf) -> bool:
    root = pdf.Root
    acroform = root.get("/AcroForm")
    if not acroform:
        return False
    return "/XFA" in acroform


def __has_file_size_exceeded(path: Path, max_pdf_size: int) -> bool:
    size = path.stat().st_size
    if size <= 0 or size > max_pdf_size:
        return True

    return True


def __has_invalid_header(path: Path) -> bool:
    with path.open("rb") as f:
        if f.read(5) != b"%PDF-":
            return True

    return False


def __has_no_pages(pdf: pikepdf.Pdf) -> bool:
    return len(pdf.pages) <= 0


def _pdf_has_suspicious_content(path: str | Path, max_pdf_size: int) -> list[str]:
    path = Path(path)

    findings = []

    if __has_file_size_exceeded(path, max_pdf_size):
        findings.append(
            "File size exceeded - adjust max_pdf_size parameter to allow larger files"
        )

    if __has_invalid_header(path):
        findings.append("Invalid PDF header, could be corrupted or not a PDF")
        return findings

    with pikepdf.open(path) as pdf:
        if __has_no_pages(pdf):
            findings.append("No pages in PDF")

        if __has_javascript(pdf):
            findings.append("JavaScript detected")

        # if __has_launch_action(pdf):
        #     findings.append("Launch action detected")

        if __has_embedded_files(pdf):
            findings.append("Embedded files detected")

        if __has_rich_media(pdf):
            findings.append("Rich media detected")

        if __has_xfa(pdf):
            findings.append("XFA forms detected")

    return findings
