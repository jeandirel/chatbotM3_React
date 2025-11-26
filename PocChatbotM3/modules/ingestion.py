import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from PyPDF2 import PdfReader
import docx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngestionService:
    """
    Service responsible for loading and extracting text from various file formats.
    """

    def load_documents(self, input_dir: str) -> List[Dict[str, any]]:
        """
        Recursively loads and parses files from a directory.
        Returns a list of dictionaries representing documents.
        """
        documents = []
        input_path = Path(input_dir)
        if not input_path.is_dir():
            logger.error(f"Input directory '{input_dir}' does not exist.")
            return []

        logger.info(f"Scanning source directory: {input_dir}")
        for file_path in input_path.rglob("*.*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(input_path)
                source_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
                ext = file_path.suffix.lower()
                text = None

                logger.debug(f"Processing file: {relative_path} (Source folder: {source_folder})")

                if ext == ".pdf":
                    text = self._extract_text_from_pdf(str(file_path))
                elif ext == ".docx":
                    text = self._extract_text_from_docx(str(file_path))
                elif ext == ".txt":
                    text = self._extract_text_from_txt(str(file_path))
                elif ext == ".csv":
                    text = self._extract_text_from_csv(str(file_path))
                elif ext in [".xlsx", ".xls"]:
                    text = self._extract_text_from_excel(str(file_path))
                else:
                    logger.warning(f"Unsupported file type ignored: {relative_path}")
                    continue

                if text:
                    documents.append({
                        "page_content": text,
                        "metadata": {
                            "source": str(relative_path),
                            "filename": file_path.name,
                            "category": source_folder,
                            "full_path": str(file_path.resolve())
                        }
                    })
                else:
                    logger.warning(f"No text could be extracted from {relative_path}")

        logger.info(f"{len(documents)} documents loaded and parsed.")
        return documents

    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        try:
            reader = PdfReader(file_path)
            text = "".join(page.extract_text() + "\n" for page in reader.pages if page.extract_text())
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
            return None

    def _extract_text_from_docx(self, file_path: str) -> Optional[str]:
        try:
            doc = docx.Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs if para.text)
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            return None

    def _extract_text_from_txt(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text
        except Exception as e:
            logger.error(f"Error extracting TXT {file_path}: {e}")
            return None

    def _extract_text_from_csv(self, file_path: str) -> Optional[str]:
        try:
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1')
            except Exception:
                try:
                    df = pd.read_csv(file_path, sep=';')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, sep=';', encoding='latin1')
                except Exception as e:
                    logger.error(f"Could not read CSV {file_path}: {e}")
                    return None
            return df.to_string()
        except Exception as e:
            logger.error(f"Error extracting CSV {file_path}: {e}")
            return None

    def _extract_text_from_excel(self, file_path: str) -> Optional[str]:
        try:
            df = pd.read_excel(file_path, sheet_name=None)
            text = ""
            if isinstance(df, dict):
                for sheet_name, sheet_df in df.items():
                    text += f"--- Sheet: {sheet_name} ---\n{sheet_df.to_string()}\n\n"
            else:
                text = df.to_string()
            return text
        except Exception as e:
            logger.error(f"Error extracting Excel {file_path}: {e}")
            return None
