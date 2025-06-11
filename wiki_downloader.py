#!/usr/bin/env python3
"""
MediaWiki page downloader with page limit and category filtering.
"""

import requests
import json
import os
import time
import argparse
import re
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Dict, Any


class WikiDownloader:
    def __init__(self, wiki_url: str, output_dir: str = "wiki_pages"):
        """
        Initialize the wiki downloader.
        
        Args:
            wiki_url: Base URL of the MediaWiki instance (e.g., https://en.wikipedia.org)
            output_dir: Directory to save downloaded pages
        """
        # Do not strip trailing slash to preserve subdirectories in base url
        self.wiki_url = wiki_url
        # Ensure api.php is joined correctly, preserving subdirectories
        parsed = urlparse(self.wiki_url)
        if not parsed.path.endswith('/'):
            # Ensure trailing slash for correct urljoin behavior
            base_url = self.wiki_url + '/'
        else:
            base_url = self.wiki_url
        self.api_url = urljoin(base_url, 'api.php')
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikiDownloader/1.0 (https://example.com/contact)'
        })
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def get_pages_in_category(self, category: str, limit: int) -> List[str]:
        """
        Get list of page titles in a specific category.
        
        Args:
            category: Category name (without "Category:" prefix)
            limit: Maximum number of pages to retrieve
            
        Returns:
            List of page titles
        """
        pages = []
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': min(limit, 500),  # API limit is 500 per request
            'cmtype': 'page',
            'format': 'json'
        }
        
        while len(pages) < limit:
            response = self.session.get(self.api_url, params=params)
            
            # Check if we got a valid response
            if response.status_code != 200:
                raise Exception(f"HTTP error {response.status_code}: {response.text[:200]}")
            
            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"API URL: {self.api_url}")
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text[:500]}")
                raise Exception(f"Invalid JSON response from API")
            
            if 'error' in data:
                raise Exception(f"API error: {data['error']['info']}")
            
            category_members = data.get('query', {}).get('categorymembers', [])
            for member in category_members:
                if len(pages) >= limit:
                    break
                pages.append(member['title'])
            
            if 'continue' not in data or len(pages) >= limit:
                break
                
            params.update(data['continue'])
            time.sleep(0.1)  # Rate limiting
        
        return pages[:limit]
    
    def get_all_pages(self, limit: int) -> List[str]:
        """
        Get list of all page titles (up to limit).
        
        Args:
            limit: Maximum number of pages to retrieve
            
        Returns:
            List of page titles
        """
        pages = []
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': min(limit, 500),  # API limit is 500 per request
            'format': 'json'
        }
        
        while len(pages) < limit:
            print(f"Requesting URL: {self.api_url} with params: {params}")
            response = self.session.get(self.api_url, params=params)
            
            # Check if we got a valid response
            if response.status_code != 200:
                raise Exception(f"HTTP error {response.status_code}: {response.text[:200]}")
            
            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"API URL: {self.api_url}")
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text[:500]}")
                raise Exception(f"Invalid JSON response from API. The API might be at a different path or the wiki might require authentication.")
            
            if 'error' in data:
                raise Exception(f"API error: {data['error']['info']}")
            
            all_pages = data.get('query', {}).get('allpages', [])
            for page in all_pages:
                if len(pages) >= limit:
                    break
                pages.append(page['title'])
            
            if 'continue' not in data or len(pages) >= limit:
                break
                
            params.update(data['continue'])
            time.sleep(0.1)  # Rate limiting
        
        return pages[:limit]
    
    def is_redirect(self, title: str) -> bool:
        """
        Check if a page is a redirect.
        
        Args:
            title: Page title to check
            
        Returns:
            True if page is a redirect, False otherwise
        """
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'info',
            'format': 'json',
            'formatversion': '2'
        }
        
        response = self.session.get(self.api_url, params=params)
        
        if response.status_code != 200:
            return False  # Assume not redirect on error
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            return False  # Assume not redirect on parse error
        
        pages = data.get('query', {}).get('pages', [])
        if pages:
            page = pages[0]
            # Check if page has redirect property
            return 'redirect' in page
        
        return False

    def download_page(self, title: str) -> Dict[str, Any]:
        """
        Download a single page by title.
        
        Args:
            title: Page title
            
        Returns:
            Dictionary containing page data with HTML content
            
        Raises:
            Exception: If page is a redirect or cannot be downloaded
        """
        # First check if this is a redirect
        if self.is_redirect(title):
            raise Exception(f"Page '{title}' is a redirect - skipping")
        
        # Get the parsed HTML content
        params = {
            'action': 'parse',
            'page': title,
            'prop': 'text|displaytitle',
            'format': 'json',
            'formatversion': '2'
        }
        
        response = self.session.get(self.api_url, params=params)
        
        # Check if we got a valid response
        if response.status_code != 200:
            raise Exception(f"HTTP error {response.status_code}: {response.text[:200]}")
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"API URL: {self.api_url}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            raise Exception(f"Invalid JSON response from API")
        
        if 'error' in data:
            raise Exception(f"API error: {data['error']['info']}")
        
        parse_data = data.get('parse', {})
        if not parse_data:
            raise Exception(f"Page '{title}' not found or could not be parsed")
        
        # Get additional page info
        info_params = {
            'action': 'query',
            'prop': 'info',
            'titles': title,
            'inprop': 'url',
            'format': 'json',
            'formatversion': '2'
        }
        
        info_response = self.session.get(self.api_url, params=info_params)
        info_data = info_response.json()
        
        page_info = info_data.get('query', {}).get('pages', [{}])[0]
        
        return {
            'title': parse_data.get('title', title),
            'pageid': parse_data.get('pageid', 0),
            'url': page_info.get('fullurl', ''),
            'content': parse_data.get('text', ''),
            'displaytitle': parse_data.get('displaytitle', title)
        }
    
    def clean_html_content(self, html_content: str, page_title: str = '') -> str:
        """
        Clean HTML content by removing unwanted elements and adding page title.
        
        Args:
            html_content: Raw HTML content from MediaWiki
            page_title: Page title to add as H1 heading
            
        Returns:
            Cleaned HTML content with H1 title
        """
        if not html_content:
            return ''
        
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove enclosing div with class "mw-parser-output"
        # Look for the opening div tag
        parser_output_pattern = r'<div\s+class="mw-parser-output"[^>]*>(.*?)</div>'
        match = re.search(parser_output_pattern, html_content, re.DOTALL)
        
        if match:
            # Extract content inside the mw-parser-output div
            html_content = match.group(1)
        
        # Trim leading/trailing whitespace
        html_content = html_content.strip()
        
        # Add H1 with page title at the beginning only if there's content
        if page_title and html_content:
            # Escape any HTML characters in the title
            escaped_title = page_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            h1_element = f'<h1>{escaped_title}</h1>'
            
            # Add H1 at the beginning with a newline
            html_content = f'{h1_element}\n{html_content}'
        
        return html_content

    def get_filepath(self, page_data: Dict[str, Any]) -> str:
        """
        Generate the filepath for a page without saving it.
        
        Args:
            page_data: Dictionary containing page data
            
        Returns:
            Path where the file would be saved
        """
        # Sanitize filename - remove/replace problematic characters
        filename = page_data['title']
        
        # Replace problematic characters with underscores
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Handle empty filename
        if not filename:
            filename = f"page_{page_data.get('pageid', 'unknown')}"
        
        # Limit filename length (most filesystems support 255 chars)
        max_length = 200  # Leave room for .html extension and potential numbering
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip()
        
        filename = f"{filename}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        return filepath

    def save_page(self, page_data: Dict[str, Any]) -> str:
        """
        Save cleaned HTML content to file.
        
        Args:
            page_data: Dictionary containing page data
            
        Returns:
            Path to saved file
        """
        filepath = self.get_filepath(page_data)
        
        # Clean the HTML content before saving
        raw_content = page_data.get('content', '')
        page_title = page_data.get('title', '')
        cleaned_content = self.clean_html_content(raw_content, page_title)
        
        # Save the cleaned HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return filepath
    
    def download_pages(self, limit: int, category: Optional[str] = None, force: bool = False) -> None:
        """
        Download multiple pages with optional category filter.
        
        Args:
            limit: Maximum number of pages to download
            category: Optional category to filter pages
            force: If True, redownload files even if they already exist
        """
        print(f"Starting download from {self.wiki_url}")
        print(f"Output directory: {self.output_dir}")
        
        downloaded = 0
        failed = 0
        redirects_skipped = 0
        skipped_existing = 0
        page_index = 0
        
        # Get initial batch of pages
        if category:
            print(f"Fetching pages from category: {category}")
            pages = self.get_pages_in_category(category, limit * 3)  # Get extra to account for redirects
        else:
            print(f"Fetching all pages")
            pages = self.get_all_pages(limit * 3)  # Get extra to account for redirects
        
        print(f"Found {len(pages)} candidate pages")
        if not force:
            print("Skipping files that already exist (use --force to redownload)")
        
        while downloaded < limit and page_index < len(pages):
            title = pages[page_index]
            page_index += 1
            
            try:
                # Check if file already exists (unless force is True)
                if not force:
                    # We need to get basic page data to determine the filepath
                    temp_page_data = {'title': title, 'pageid': 0}
                    potential_filepath = self.get_filepath(temp_page_data)
                    
                    if os.path.exists(potential_filepath):
                        print(f"[{downloaded + 1}/{limit}] Skipping existing: {title}")
                        print(f"  File exists: {potential_filepath}")
                        skipped_existing += 1
                        downloaded += 1  # Count as "downloaded" since we have the file
                        continue
                
                print(f"[{downloaded + 1}/{limit}] Downloading: {title}")
                
                # Check if it's a redirect first
                if self.is_redirect(title):
                    print(f"  Redirect detected - saving empty file")
                    # Create empty page data for redirect
                    redirect_page_data = {
                        'title': title,
                        'pageid': 0,
                        'url': '',
                        'content': '',
                        'displaytitle': title
                    }
                    filepath = self.save_page(redirect_page_data)
                    print(f"  Saved empty redirect: {filepath}")
                    redirects_skipped += 1
                else:
                    # Download normal page
                    page_data = self.download_page(title)
                    filepath = self.save_page(page_data)
                    print(f"  Saved to: {filepath}")
                
                downloaded += 1
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"  Error: {e}")
                failed += 1
        
        print(f"\nDownload complete!")
        print(f"Successfully downloaded: {downloaded - skipped_existing} pages")
        print(f"Skipped existing files: {skipped_existing} pages")
        print(f"Redirects skipped: {redirects_skipped} pages")
        print(f"Failed: {failed} pages")


def main():
    parser = argparse.ArgumentParser(
        description="Download pages from a MediaWiki wiki"
    )
    parser.add_argument(
        'wiki_url',
        help='Base URL of the MediaWiki instance (e.g., https://en.wikipedia.org)'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=10,
        help='Maximum number of pages to download (default: 10)'
    )
    parser.add_argument(
        '-c', '--category',
        help='Download only pages from this category'
    )
    parser.add_argument(
        '-o', '--output',
        default='wiki_pages',
        help='Output directory for downloaded pages (default: wiki_pages)'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force redownload of files even if they already exist'
    )
    
    args = parser.parse_args()
    
    downloader = WikiDownloader(args.wiki_url, args.output)
    downloader.download_pages(args.limit, args.category, args.force)


if __name__ == '__main__':
    main()