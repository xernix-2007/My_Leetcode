"""Main LeetCode PDF generator.

The repository historically had two PDF layouts. Keep generate_pdf.py as the
primary entry point, but use the readable layout implemented by
generate_pdf_simple.py so both generated PDFs stay consistent.
"""

import generate_pdf_simple

generate_pdf_simple.OUTPUT = generate_pdf_simple.ROOT / "LeetCode_Notes.pdf"

if __name__ == "__main__":
    generate_pdf_simple.build()
