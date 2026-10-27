import io
import logging

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except ImportError:
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')

def _deny_fetch(url, *args, **kwargs):
    raise ValueError(f'External resource blocked: {url}')

def _safe_fetcher():
    #reports are self-contained; refuse file:// and network fetches (SSRF / local file read)
    try:
        from weasyprint import URLFetcher   # WeasyPrint 68+
        return URLFetcher(allowed_protocols=['data'])
    except ImportError:
        return _deny_fetch

def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not WEASYPRINT_INSTALLED:
        raise ImportError("WeasyPrint is not installed. PDF generation unavailable.")
        
    documents = []
    
    # Render all 3 HTML strings to WeasyPrint Document objects
    for name, html_str in html_docs.items():
        doc = HTML(string=html_str, url_fetcher=_safe_fetcher()).render()
        documents.append(doc)
    
    # Merge them into the first document
    first_doc = documents[0]
    for other_doc in documents[1:]:
        for page in other_doc.pages:
            first_doc.pages.append(page)
            
    # Write combined PDF bytes
    pdf_bytes = first_doc.write_pdf()
    return pdf_bytes