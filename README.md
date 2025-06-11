# WikiExport3

A Python tool for downloading pages from MediaWiki instances with support for page limits and category filtering, plus HTML to Markdown conversion.

## Features

- Download pages from any MediaWiki instance
- Filter pages by category
- Configurable page limits
- Rate limiting to be respectful to servers
- HTML output format with clean styling
- Support for custom wiki installations
- Automatic redirect detection and exclusion
- HTML to Markdown conversion for downloaded pages

## Basic Usage
```bash
python wiki_downloader.py https://en.wikipedia.org --limit 10
```

## Installation

### Using pip (recommended)

```bash
pip install -e .
```

### Development installation

```bash
# Clone the repository
git clone <your-repo-url>
cd wikiexport3

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e .[dev]
```

## Usage

### Wiki Downloader

#### Command Line

```bash
# Download 10 pages from Wikipedia
python wiki_downloader.py https://en.wikipedia.org --limit 10

# Download pages from a specific category
python wiki_downloader.py https://en.wikipedia.org --limit 5 --category "Python (programming language)"

# Download from a custom wiki
python wiki_downloader.py https://brulescorp.com/brwiki2 --limit 3 --output my_pages

# Get help
python wiki_downloader.py --help
```

#### As a Python Module

```python
from wiki_downloader import WikiDownloader

# Initialize downloader
downloader = WikiDownloader("https://en.wikipedia.org", "output_folder")

# Download all pages (up to limit)
downloader.download_pages(limit=5)

# Download from specific category
downloader.download_pages(limit=3, category="Technology")
```

### HTML to Markdown Converter

#### Command Line

```bash
# Convert all HTML files in wiki_pages directory
python html_to_markdown.py

# Convert with custom input/output directories
python html_to_markdown.py --input my_html_pages --output my_markdown_pages

# Convert a single file
python html_to_markdown.py --file wiki_pages/Main_Page.html

# Get help
python html_to_markdown.py --help
```

#### As a Python Module

```python
from html_to_markdown import HTMLToMarkdownConverter

# Initialize converter
converter = HTMLToMarkdownConverter("wiki_pages", "markdown_pages")

# Convert all HTML files
converter.convert_all_files()

# Convert single file
converter.convert_file("wiki_pages/Main_Page.html")
```

## Command Line Options

### Wiki Downloader
- `wiki_url`: Base URL of the MediaWiki instance (required)
- `-l, --limit`: Maximum number of pages to download (default: 10)
- `-c, --category`: Download only pages from this category
- `-o, --output`: Output directory for downloaded pages (default: wiki_pages)

### HTML to Markdown Converter
- `-i, --input`: Input directory containing HTML files (default: wiki_pages)
- `-o, --output`: Output directory for Markdown files (default: markdown_pages)
- `-f, --file`: Convert a specific HTML file instead of entire directory

## Output Formats

### HTML Output (from wiki_downloader.py)

Pages are saved as HTML files containing cleaned, rendered content from MediaWiki:

- Pure HTML content as rendered by MediaWiki
- H1 heading with page title automatically added at the top
- HTML comments automatically removed
- MediaWiki wrapper divs (mw-parser-output) stripped away
- Fully processed content (links, tables, images, etc.)
- Ready to be embedded in other documents or websites
- Preserves all MediaWiki formatting and structure

### Markdown Output (from html_to_markdown.py)

HTML files are converted to clean Markdown format:

- Standard Markdown syntax (ATX-style headings with #)
- Tables converted to Markdown table format
- Links and images preserved with Markdown syntax
- Bold, italic, and other formatting converted
- Code blocks and inline code preserved
- Lists converted to Markdown format
- Clean output with minimal whitespace

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
flake8 wiki_downloader.py html_to_markdown.py
black wiki_downloader.py html_to_markdown.py

# Type checking
mypy wiki_downloader.py html_to_markdown.py
```

### VS Code Launch Configurations

The project includes VS Code launch configurations for easy debugging:

- **Wiki Downloader - Default**: Test with your custom wiki
- **Wiki Downloader - Debug Mode**: Minimal setup for debugging
- **HTML to Markdown - Convert All**: Convert all HTML files to Markdown
- **HTML to Markdown - Single File**: Convert one specific file

## Complete Workflow Example

```bash
# Step 1: Download wiki pages as HTML
python wiki_downloader.py https://en.wikipedia.org --limit 5 --output my_wiki

# Step 2: Convert HTML to Markdown
python html_to_markdown.py --input my_wiki --output my_markdown

# Result: You now have both HTML and Markdown versions of the wiki pages
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Rate Limiting

The wiki downloader includes built-in rate limiting (0.1-0.5 second delays) to be respectful to MediaWiki servers. Please use responsibly and consider the server load when downloading large numbers of pages. 