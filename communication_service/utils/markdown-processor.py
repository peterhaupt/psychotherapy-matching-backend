"""Markdown processing utilities."""
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup
from typing import Optional

# Initialize markdown processor with useful plugins
md = MarkdownIt("commonmark", {"breaks": True, "html": True})
md.enable(["table", "strikethrough"])

def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        HTML formatted text
    """
    return md.render(markdown_text)

def strip_html(html_text: str) -> str:
    """Strip HTML tags to create plain text.
    
    Args:
        html_text: HTML formatted text
        
    Returns:
        Plain text without HTML tags
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n').strip()

def wrap_with_styling(html_content: str, add_footer: bool = True) -> str:
    """Wrap HTML content with styling and optional footer.
    
    Args:
        html_content: Raw HTML content
        add_footer: Whether to add legal footer
        
    Returns:
        Styled HTML with optional footer
    """
    from shared.config import get_config
    config = get_config()
    
    footer_html = ""
    if add_footer and getattr(config, 'EMAIL_ADD_LEGAL_FOOTER', True):
        footer_html = get_legal_footer()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{ color: #2c5aa0; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_content}
        </div>
        {footer_html}
    </body>
    </html>
    """

def get_legal_footer() -> str:
    """Get the legal footer HTML."""
    return """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666;">
        <p><strong>Datenschutzhinweis:</strong> Diese E-Mail enthält vertrauliche und/oder gesundheitsbezogene Informationen und ist ausschließlich für den Adressaten bestimmt.</p>
        <p>© 2025 Curavani Therapievermittlung GmbH<br>
        Musterstraße 123, 12345 Berlin<br>
        <a href="https://curavani.de/datenschutz">Datenschutz</a> | 
        <a href="https://curavani.de/impressum">Impressum</a> | 
        <a href="https://curavani.de/kontakt">Kontakt</a></p>
    </div>
    """