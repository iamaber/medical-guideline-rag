import PyPDF2

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    if not text:
        return chunks
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def process_pdf_to_chunks(pdf_path, chunk_size=1000, overlap=100):
    full_text = extract_text_from_pdf(pdf_path)
    return chunk_text(full_text, chunk_size, overlap)