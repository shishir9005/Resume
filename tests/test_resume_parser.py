import io

import pytest
from docx import Document

from backend.core.config import MAX_FILE_SIZE_BYTES
from backend.services.resume_parser import (
    FileParsingError,
    FileValidationError,
    extract_text,
    parse_resume_file,
    validate_file,
)


def make_docx(*paragraphs: str) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_docx_text_is_extracted():
    text, metadata = parse_resume_file(make_docx('Jane Doe', 'Skills: Python, SQL'), 'cv.docx')
    assert 'Jane Doe' in text and 'Python, SQL' in text
    assert metadata['file_type'] == 'docx'


def test_empty_file_is_rejected_with_clear_message():
    is_valid, message, file_type = validate_file(b'', 'cv.pdf')
    assert not is_valid and file_type is None
    assert 'empty' in message

    with pytest.raises(FileValidationError, match='empty'):
        parse_resume_file(b'', 'cv.pdf')


def test_oversized_file_is_rejected():
    is_valid, message, _ = validate_file(b'0' * (MAX_FILE_SIZE_BYTES + 1), 'cv.pdf')
    assert not is_valid
    assert 'exceeds' in message


def test_plain_text_file_is_rejected():
    with pytest.raises(FileValidationError, match='Unsupported file type'):
        parse_resume_file(b'just some plain text, not a resume file', 'cv.txt')


def test_legacy_doc_gives_conversion_hint():
    with pytest.raises(FileParsingError, match='convert'):
        extract_text(b'', 'doc')
