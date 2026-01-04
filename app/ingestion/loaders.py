"""
Document loaders for various file formats (PDF, TXT, MD).
Factory pattern for extensibility.
"""

from pathlib import Path
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import PyPDF2
import io


class DocumentLoader(ABC):
    """Abstract base class for document loaders."""
    
    @abstractmethod
    def load(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load document from bytes.
        
        Args:
            content: File content as bytes
            filename: Original filename
            metadata: Optional metadata dict
            
        Returns:
            Dict with 'text' and 'metadata' keys
        """
        pass


class PDFLoader(DocumentLoader):
    """Loader for PDF documents."""
    
    def load(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract text from PDF."""
        try:
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            
            # Extract PDF metadata
            pdf_metadata = {
                "source": filename,
                "file_type": "pdf",
                "page_count": len(reader.pages),
                **(metadata or {})
            }
            
            if reader.metadata:
                if reader.metadata.title:
                    pdf_metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    pdf_metadata["author"] = reader.metadata.author
            
            return {
                "text": full_text,
                "metadata": pdf_metadata
            }
        except Exception as e:
            raise ValueError(f"Failed to load PDF {filename}: {str(e)}")


class TextLoader(DocumentLoader):
    """Loader for plain text files."""
    
    def load(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract text from TXT file."""
        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            
            text_metadata = {
                "source": filename,
                "file_type": "txt",
                "char_count": len(text),
                **(metadata or {})
            }
            
            return {
                "text": text,
                "metadata": text_metadata
            }
        except Exception as e:
            raise ValueError(f"Failed to load TXT {filename}: {str(e)}")


class MarkdownLoader(DocumentLoader):
    """Loader for Markdown files."""
    
    def load(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract text from Markdown file."""
        try:
            # Decode as text (Markdown is plain text)
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            
            md_metadata = {
                "source": filename,
                "file_type": "markdown",
                "char_count": len(text),
                **(metadata or {})
            }
            
            return {
                "text": text,
                "metadata": md_metadata
            }
        except Exception as e:
            raise ValueError(f"Failed to load Markdown {filename}: {str(e)}")


class DocumentLoaderFactory:
    """Factory for creating appropriate document loaders."""
    
    _loaders = {
        ".pdf": PDFLoader,
        ".txt": TextLoader,
        ".md": MarkdownLoader,
        ".markdown": MarkdownLoader,
    }
    
    @classmethod
    def get_loader(cls, filename: str) -> DocumentLoader:
        """
        Get appropriate loader based on file extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            DocumentLoader instance
            
        Raises:
            ValueError: If file type is not supported
        """
        ext = Path(filename).suffix.lower()
        loader_class = cls._loaders.get(ext)
        
        if not loader_class:
            supported = ", ".join(cls._loaders.keys())
            raise ValueError(
                f"Unsupported file type: {ext}. Supported types: {supported}"
            )
        
        return loader_class()
    
    @classmethod
    def supported_extensions(cls) -> List[str]:
        """Return list of supported file extensions."""
        return list(cls._loaders.keys())
