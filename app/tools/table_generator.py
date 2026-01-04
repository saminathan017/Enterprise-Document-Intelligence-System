"""
Table generator tool for structured data presentation.
Formats extracted data into markdown tables.
"""

from typing import List, Dict, Any
from langchain_core.tools import tool


class TableGeneratorTool:
    """Tool for generating markdown tables from structured data."""
    
    def generate_table(
        self,
        data: List[Dict[str, Any]],
        headers: List[str] = None
    ) -> str:
        """
        Generate markdown table from data.
        
        Args:
            data: List of dicts representing rows
            headers: Optional list of column headers
            
        Returns:
            Markdown formatted table
        """
        if not data:
            return "No data available for table generation."
        
        # Extract headers from first row if not provided
        if not headers:
            headers = list(data[0].keys())
        
        # Build table
        table_lines = []
        
        # Header row
        table_lines.append("| " + " | ".join(headers) + " |")
        
        # Separator row
        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Data rows
        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            table_lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(table_lines)
    
    def format_comparison_table(
        self,
        categories: List[str],
        metrics: Dict[str, List[Any]]
    ) -> str:
        """
        Create a comparison table for metrics across categories.
        
        Args:
            categories: List of category names (e.g., Q1, Q2, Q3)
            metrics: Dict mapping metric names to lists of values
            
        Returns:
            Markdown formatted comparison table
        """
        if not categories or not metrics:
            return "Insufficient data for comparison table."
        
        # Build header
        headers = ["Metric"] + categories
        table_lines = []
        table_lines.append("| " + " | ".join(headers) + " |")
        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Build rows
        for metric_name, values in metrics.items():
            row_values = [metric_name] + [str(v) for v in values]
            table_lines.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join(table_lines)
    
    def parse_and_format(self, text: str) -> str:
        """
        Attempt to parse structured data from text and format as table.
        
        This is a simplified version - in production, you'd use more
        sophisticated parsing (regex, NLP, etc.).
        
        Args:
            text: Text potentially containing structured data
            
        Returns:
            Markdown table or message if parsing failed
        """
        # This is a placeholder - the actual table generation
        # will be handled by the LLM using the RAG chain with
        # the TABLE_GENERATION_PROMPT
        return text


@tool
def table_generator(text: str) -> str:
    """
    Generate well-formatted markdown tables from data. Use when the user 
    requests comparisons, summaries, or structured data presentation. 
    Particularly useful for financial metrics, trend analysis, and comparative reports.
    
    Args:
        text: Text potentially containing structured data
        
    Returns:
        Markdown table or message if parsing failed
    """
    table_tool = TableGeneratorTool()
    return table_tool.parse_and_format(text)


def create_table_tool():
    """Create table generation tool."""
    return table_generator
