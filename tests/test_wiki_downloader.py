#!/usr/bin/env python3
"""
Tests for wiki_downloader module
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_downloader import WikiDownloader


class TestWikiDownloader:
    """Test cases for WikiDownloader class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.wiki_url = "https://example.com/wiki"
        self.downloader = WikiDownloader(self.wiki_url, self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test WikiDownloader initialization"""
        assert self.downloader.wiki_url == self.wiki_url
        assert self.downloader.output_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
        assert self.downloader.api_url == "https://example.com/wiki/api.php"
    
    def test_init_with_trailing_slash(self):
        """Test WikiDownloader initialization with trailing slash in URL"""
        downloader = WikiDownloader("https://example.com/wiki/", self.temp_dir)
        assert downloader.api_url == "https://example.com/wiki/api.php"
    
    def test_init_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist"""
        new_temp_dir = os.path.join(self.temp_dir, "new_dir")
        downloader = WikiDownloader(self.wiki_url, new_temp_dir)
        assert os.path.exists(new_temp_dir)
    
    def test_save_page(self):
        """Test saving page data to file"""
        page_data = {
            'title': 'Test Page',
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': 'Test content',
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        filepath = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('Test Page.json')
        
        # Verify file content
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data == page_data
    
    def test_save_page_sanitizes_filename(self):
        """Test that page titles with special characters are sanitized"""
        page_data = {
            'title': 'Test/Page:With\\Special*Characters?<>"|',
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': 'Test content',
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        filepath = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath)
        # All special characters should be replaced with underscores
        assert 'Test_Page_With_Special_Characters_______.json' in filepath
    
    def test_save_page_handles_empty_title(self):
        """Test that empty or whitespace-only titles are handled"""
        page_data = {
            'title': '   ',  # Only whitespace
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': 'Test content',
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        filepath = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath)
        assert 'page_12345.json' in filepath
    
    def test_save_page_handles_long_filename(self):
        """Test that very long filenames are truncated"""
        long_title = 'A' * 250  # Very long title
        page_data = {
            'title': long_title,
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': 'Test content',
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        filepath = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath)
        filename = os.path.basename(filepath)
        # Should be truncated to reasonable length
        assert len(filename) <= 205  # 200 + ".json"
    
    def test_save_page_handles_duplicate_filenames(self):
        """Test that duplicate filenames get unique numbers"""
        page_data = {
            'title': 'Duplicate Page',
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': 'Test content',
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        # Save first file
        filepath1 = self.downloader.save_page(page_data)
        
        # Save second file with same title
        page_data['pageid'] = 67890
        filepath2 = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)
        assert filepath1 != filepath2
        assert 'Duplicate Page.json' in filepath1
        assert 'Duplicate Page_1.json' in filepath2
    
    @patch('wiki_downloader.requests.Session.get')
    def test_get_all_pages_success(self, mock_get):
        """Test successful retrieval of all pages"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'allpages': [
                    {'title': 'Page 1'},
                    {'title': 'Page 2'},
                    {'title': 'Page 3'}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        pages = self.downloader.get_all_pages(3)
        
        assert len(pages) == 3
        assert pages == ['Page 1', 'Page 2', 'Page 3']
    
    @patch('wiki_downloader.requests.Session.get')
    def test_get_all_pages_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as excinfo:
            self.downloader.get_all_pages(1)
        
        assert "HTTP error 404" in str(excinfo.value)
    
    @patch('wiki_downloader.requests.Session.get')
    def test_get_pages_in_category_success(self, mock_get):
        """Test successful retrieval of pages in category"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'categorymembers': [
                    {'title': 'Category Page 1'},
                    {'title': 'Category Page 2'}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        pages = self.downloader.get_pages_in_category('Test Category', 2)
        
        assert len(pages) == 2
        assert pages == ['Category Page 1', 'Category Page 2']


if __name__ == '__main__':
    pytest.main([__file__]) 