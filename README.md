# WikiExport3

A Python tool for downloading pages from MediaWiki instances with support for page limits and category filtering.

## Features

- Download pages from any MediaWiki instance
- Filter pages by category
- Configurable page limits
- Rate limiting to be respectful to servers
- HTML output format with clean styling
- Support for custom wiki installations
- Automatic redirect detection and exclusion

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

### Command Line

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

### As a Python Module

```python
from wiki_downloader import WikiDownloader

# Initialize downloader
downloader = WikiDownloader("https://en.wikipedia.org", "output_folder")

# Download all pages (up to limit)
downloader.download_pages(limit=5)

# Download from specific category
downloader.download_pages(limit=3, category="Technology")
```

## Command Line Options

- `wiki_url`: Base URL of the MediaWiki instance (required)
- `-l, --limit`: Maximum number of pages to download (default: 10)
- `-c, --category`: Download only pages from this category
- `-o, --output`: Output directory for downloaded pages (default: wiki_pages)

## Output Format

Pages are saved as HTML files containing the bare rendered content from MediaWiki:

- Pure HTML content as rendered by MediaWiki
- No additional wrapper HTML or styling
- Fully processed content (links, tables, images, etc.)
- Ready to be embedded in other documents or websites
- Preserves all MediaWiki formatting and structure

Each file contains only the content portion of the wiki page, making it easy to integrate into other HTML documents or content management systems.

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
flake8 wiki_downloader.py
black wiki_downloader.py

# Type checking
mypy wiki_downloader.py
```

### VS Code Launch Configurations

The project includes VS Code launch configurations for easy debugging:

- **Wiki Downloader - Default**: Test with your custom wiki
- **Wiki Downloader - Debug Mode**: Minimal setup for debugging

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

The tool includes built-in rate limiting (0.1-0.5 second delays) to be respectful to MediaWiki servers. Please use responsibly and consider the server load when downloading large numbers of pages. 