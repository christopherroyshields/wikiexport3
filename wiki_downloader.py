#!/usr/bin/env python3
"""
MediaWiki page downloader with page limit and category filtering.
"""

import requests
import json
import os
import time
import argparse
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
    
    def save_page(self, page_data: Dict[str, Any]) -> str:
        """
        Save bare HTML content to file.
        
        Args:
            page_data: Dictionary containing page data
            
        Returns:
            Path to saved file
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
        
        # Ensure unique filename if file already exists
        base_filename = filename
        counter = 1
        while os.path.exists(os.path.join(self.output_dir, f"{filename}.html")):
            filename = f"{base_filename}_{counter}"
            counter += 1
        
        filename = f"{filename}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save only the bare HTML content from MediaWiki
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(page_data.get('content', ''))
        
        return filepath
    
    def download_pages(self, limit: int, category: Optional[str] = None) -> None:
        """
        Download multiple pages with optional category filter.
        
        Args:
            limit: Maximum number of pages to download
            category: Optional category to filter pages
        """
        print(f"Starting download from {self.wiki_url}")
        print(f"Output directory: {self.output_dir}")
        
        if category:
            print(f"Fetching pages from category: {category}")
            pages = self.get_pages_in_category(category, limit)
        else:
            print(f"Fetching all pages (limit: {limit})")
            pages = self.get_all_pages(limit)
        
        print(f"Found {len(pages)} pages to download")
        
        downloaded = 0
        failed = 0
        redirects_skipped = 0
        
        for i, title in enumerate(pages, 1):
            try:
                print(f"[{i}/{len(pages)}] Downloading: {title}")
                page_data = self.download_page(title)
                filepath = self.save_page(page_data)
                print(f"  Saved to: {filepath}")
                downloaded += 1
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                if "is a redirect" in str(e):
                    print(f"  Skipped: {e}")
                    redirects_skipped += 1
                else:
                    print(f"  Error: {e}")
                    failed += 1
        
        print(f"\nDownload complete!")
        print(f"Successfully downloaded: {downloaded} pages")
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
    
    args = parser.parse_args()
    
    downloader = WikiDownloader(args.wiki_url, args.output)
    downloader.download_pages(args.limit, args.category)


if __name__ == '__main__':
    main()