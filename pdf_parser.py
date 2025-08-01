
import os
import PyPDF2

class PDFExtractor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_text(self):
        text = ""
        try:
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PDF read error: {e}")
        return text
