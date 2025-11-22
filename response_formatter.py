"""
Response Formatter Module
Transforms General Agent responses into readable, well-structured HTML/Markdown format
with tables, sections, and proper paragraph styling for end-user consumption.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FormattedResponse:
    """Data class for formatted responses"""
    title: str
    sections: List[Dict[str, Any]]
    html: str
    markdown: str


class ResponseFormatter:
    """
    Formats General Agent responses into readable, structured content
    with proper tables, sections, and formatting for end users.
    """

    def __init__(self):
        self.sections = []

    def format_response(self, agent_response: str, query_data: Optional[List[Dict]] = None) -> str:
        """
        Main method to format General Agent response with proper structure.
        
        Args:
            agent_response: Text response from General Agent
            query_data: Optional raw query data to extract and format into tables
            
        Returns:
            HTML-formatted response with sections, tables, and proper styling
        """
        html = '<div class="formatted-response">'
        
        # Parse the response into sections
        sections = self._parse_response_sections(agent_response)
        
        for section in sections:
            html += self._format_section(section)
        
        html += '</div>'
        return html

    def _parse_response_sections(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse response into logical sections based on markdown headers and content.
        """
        sections = []
        
        # Split by markdown headers (###, ##, #)
        lines = response.split('\n')
        current_section = {'type': 'intro', 'content': [], 'title': ''}
        
        for line in lines:
            if line.startswith('### '):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {'type': 'section', 'title': line.replace('### ', '').strip(), 'content': []}
            elif line.startswith('## '):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {'type': 'major_section', 'title': line.replace('## ', '').strip(), 'content': []}
            elif line.startswith('# '):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {'type': 'title', 'title': line.replace('# ', '').strip(), 'content': []}
            elif line.startswith('| '):
                if not current_section.get('table'):
                    current_section['table'] = []
                current_section['table'].append(line)
            else:
                current_section['content'].append(line)
        
        if current_section['content'] or current_section.get('table'):
            sections.append(current_section)
        
        return sections

    def _format_section(self, section: Dict[str, Any]) -> str:
        """Format individual section with appropriate HTML structure."""
        html = ''
        
        if section['type'] == 'title':
            html += f'<h1 class="response-title">{section["title"]}</h1>'
        elif section['type'] == 'major_section':
            html += f'<h2 class="response-heading">{section["title"]}</h2>'
        elif section['type'] == 'section':
            html += f'<h3 class="response-subheading">{section["title"]}</h3>'
        
        # Handle table content
        if section.get('table'):
            html += self._format_table(section['table'])
        
        # Handle paragraph content
        if section.get('content'):
            content_text = '\n'.join(section['content']).strip()
            if content_text:
                html += self._format_paragraphs(content_text)
        
        return html

    def _format_table(self, table_lines: List[str]) -> str:
        """Convert markdown table to HTML table."""
        if not table_lines or len(table_lines) < 2:
            return ''
        
        html = '<table class="data-table">\n<thead>\n<tr>'
        
        # Parse header
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr>\n</thead>\n<tbody>\n'
        
        # Parse rows (skip separator line)
        for line in table_lines[2:]:
            if line.strip() and '|' in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if cells:
                    html += '<tr>'
                    for cell in cells:
                        html += f'<td>{cell}</td>'
                    html += '</tr>\n'
        
        html += '</tbody>\n</table>\n'
        return html

    def _format_paragraphs(self, content: str) -> str:
        """Format text content into readable paragraphs with proper styling."""
        html = ''
        
        # Split by double newlines for paragraph breaks
        paragraphs = re.split(r'\n\s*\n', content)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if it's a list
            if para.startswith('-') or para.startswith('•') or re.match(r'^\d+\.', para):
                html += self._format_list(para)
            else:
                # Regular paragraph with formatting
                para = self._apply_inline_formatting(para)
                html += f'<p class="response-paragraph">{para}</p>\n'
        
        return html

    def _format_list(self, content: str) -> str:
        """Format list items."""
        html = '<ul class="response-list">\n'
        
        items = re.split(r'\n(?=[-•]|\d+\.)', content)
        
        for item in items:
            item = re.sub(r'^[-•]\s*', '', item).strip()
            item = re.sub(r'^\d+\.\s*', '', item).strip()
            if item:
                item = self._apply_inline_formatting(item)
                html += f'<li>{item}</li>\n'
        
        html += '</ul>\n'
        return html

    def _apply_inline_formatting(self, text: str) -> str:
        """Apply inline formatting (bold, italic, code, etc.)"""
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # Italic: *text* or _text_
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        
        # Code: `text`
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        return text

    def format_for_html(self, 
                       agent_response: str,
                       query_data: Optional[List[Dict]] = None,
                       include_styles: bool = True) -> str:
        """
        Format response as complete HTML with optional embedded styles.
        
        Args:
            agent_response: General Agent text response
            query_data: Optional list of dictionaries containing query results
            include_styles: Whether to include CSS styles in output
            
        Returns:
            HTML string ready for browser display
        """
        styles = self._get_css_styles() if include_styles else ''
        formatted_content = self.format_response(agent_response, query_data)
        
        return f'{styles}\n{formatted_content}'

    @staticmethod
    def _get_css_styles() -> str:
        """Get CSS styles for formatted responses."""
        return '''
<style>
.formatted-response {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #333;
    line-height: 1.8;
    max-width: 900px;
    margin: 0 auto;
}

.response-title {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 20px 0 15px 0;
    border-bottom: 3px solid #667eea;
    padding-bottom: 10px;
}

.response-heading {
    font-size: 20px;
    font-weight: 600;
    color: #2196f3;
    margin: 20px 0 12px 0;
    border-left: 4px solid #2196f3;
    padding-left: 10px;
}

.response-subheading {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin: 15px 0 10px 0;
}

.response-paragraph {
    font-size: 15px;
    line-height: 1.8;
    color: #444;
    margin: 10px 0;
    text-align: justify;
}

.response-list {
    margin: 10px 0 10px 20px;
    padding-left: 20px;
}

.response-list li {
    margin: 8px 0;
    color: #444;
    font-size: 15px;
    line-height: 1.6;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-radius: 8px;
    overflow: hidden;
}

.data-table thead {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.data-table th {
    padding: 14px;
    text-align: left;
    font-weight: 600;
    font-size: 14px;
    text-transform: capitalize;
}

.data-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #e0e0e0;
    font-size: 14px;
    color: #555;
}

.data-table tbody tr:nth-child(odd) {
    background-color: #f9f9f9;
}

.data-table tbody tr:hover {
    background-color: #f0f0f0;
    transition: background-color 0.2s;
}

.data-table tbody tr:last-child td {
    border-bottom: none;
}

strong {
    color: #1a1a1a;
    font-weight: 600;
}

em {
    color: #666;
    font-style: italic;
}

code {
    background-color: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #d63384;
}
</style>
'''

    @staticmethod
    def create_data_summary_table(data: List[Dict], title: str = "Query Results") -> str:
        """
        Create a formatted HTML table from query results data.
        
        Args:
            data: List of dictionaries containing row data
            title: Optional title for the table
            
        Returns:
            HTML table string
        """
        if not data:
            return '<p><em>No data to display</em></p>'
        
        html = f'<h3>{title}</h3>\n<table class="data-table">\n<thead>\n<tr>'
        
        # Get headers from first row
        headers = list(data[0].keys())
        
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr>\n</thead>\n<tbody>\n'
        
        # Add rows
        for row in data:
            html += '<tr>'
            for header in headers:
                value = row.get(header, '')
                if value is None:
                    value = '<em>NULL</em>'
                html += f'<td>{value}</td>'
            html += '</tr>\n'
        
        html += '</tbody>\n</table>\n'
        return html


def format_general_agent_response(agent_text: str, 
                                  query_results: Optional[List[Dict]] = None) -> Dict[str, str]:
    """
    Convenience function to format General Agent response.
    
    Args:
        agent_text: Response text from General Agent
        query_results: Optional query results to include
        
    Returns:
        Dictionary with 'html' and 'markdown' keys
    """
    formatter = ResponseFormatter()
    html_response = formatter.format_for_html(agent_text, query_results)
    
    return {
        'html': html_response,
        'markdown': agent_text,  # Can be enhanced to convert to markdown
        'plain': agent_text
    }
