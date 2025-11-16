# core/output.py
import markdown2
from datetime import datetime

def create_html_download(analysis_markdown, title="Analyse Raadsstukken"):
    """
    Converteert de Markdown-analyse naar een volledig, opgemaakt HTML-document
    met een titel, datum en CSS-stijlen.
    """
    # Haal de huidige datum op
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")
    
    # Converteer de Markdown-analyse naar HTML
    analysis_html = markdown2.markdown(
        analysis_markdown, 
        extras=["tables", "fenced-code-blocks", "cuddled-lists", "break-on-newline"]
    )

    # Definieer een eenvoudige CSS-stylesheet voor een professionele uitstraling
    css_style = """
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            line-height: 1.6; 
            padding: 30px; 
            max-width: 800px;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        h1 { color: #222; }
        h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 5px; }
        h3 { color: #444; }
        blockquote { 
            border-left: 5px solid #ddd; 
            padding-left: 15px; 
            margin-left: 0; 
            font-style: italic; 
            color: #444; 
        }
        ul, ol { padding-left: 20px; }
    </style>
    """

    # Maak het volledige HTML-document
    html_template = f"""
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        {css_style}
    </head>
    <body>
        <h1>{title}</h1>
        <p><strong>Datum:</strong> {date_str}</p>
        <p><strong>Versie:</strong> 1.0</p>
        <hr>
        {analysis_html}
    </body>
    </html>
    """
    return html_template
