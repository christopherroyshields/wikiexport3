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
        """Test saving cleaned HTML content to file"""
        page_data = {
            'title': 'Test Page',
            'pageid': 12345,
            'url': 'https://example.com/wiki/Test_Page',
            'content': '<div class="mw-parser-output"><p>Test content</p><div>More content</div></div>',
            'displaytitle': 'Test Page'
        }
        
        filepath = self.downloader.save_page(page_data)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('Test Page.html')
        
        # Verify file contains cleaned HTML content
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        # Should contain H1 title and content without mw-parser-output wrapper
        expected_content = '<h1>Test Page</h1>\n<p>Test content</p><div>More content</div>'
        assert saved_content == expected_content
        # Should NOT contain the wrapper div
        assert 'mw-parser-output' not in saved_content
        # Should NOT contain full HTML document structure
        assert '<!DOCTYPE html>' not in saved_content
        assert '<title>' not in saved_content
    
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
        assert 'Test_Page_With_Special_Characters_______.html' in filepath
    
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
        assert 'page_12345.html' in filepath
    
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
        assert len(filename) <= 205  # 200 + ".html"
    
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
        assert 'Duplicate Page.html' in filepath1
        assert 'Duplicate Page_1.html' in filepath2
    
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
    
    @patch('wiki_downloader.requests.Session.get')
    def test_is_redirect_true(self, mock_get):
        """Test redirect detection for redirect pages"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'pages': [
                    {
                        'pageid': 12345,
                        'title': 'Redirect Page',
                        'redirect': ''  # This indicates it's a redirect
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        is_redirect = self.downloader.is_redirect('Redirect Page')
        
        assert is_redirect is True
    
    @patch('wiki_downloader.requests.Session.get')
    def test_is_redirect_false(self, mock_get):
        """Test redirect detection for regular pages"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'pages': [
                    {
                        'pageid': 12345,
                        'title': 'Regular Page'
                        # No 'redirect' property
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        is_redirect = self.downloader.is_redirect('Regular Page')
        
        assert is_redirect is False
    
    @patch('wiki_downloader.requests.Session.get')
    def test_download_page_skips_redirect(self, mock_get):
        """Test that download_page raises exception for redirect pages"""
        # Mock the redirect check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'pages': [
                    {
                        'pageid': 12345,
                        'title': 'Redirect Page',
                        'redirect': ''
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as excinfo:
            self.downloader.download_page('Redirect Page')
        
        assert "is a redirect - skipping" in str(excinfo.value)
    
    def test_clean_html_content_removes_comments(self):
        """Test that HTML comments are removed"""
        html_with_comments = '''<p>Before comment</p>
<!-- This is a comment -->
<p>After comment</p>
<!-- Another comment
spanning multiple lines -->
<p>Final content</p>'''
        
        expected = '''<p>Before comment</p>

<p>After comment</p>

<p>Final content</p>'''
        
        result = self.downloader.clean_html_content(html_with_comments)
        assert result == expected
    
    def test_clean_html_content_removes_mw_parser_output(self):
        """Test that mw-parser-output div wrapper is removed"""
        html_with_wrapper = '<div class="mw-parser-output"><p>Content inside</p><div>More content</div></div>'
        expected = '<p>Content inside</p><div>More content</div>'
        
        result = self.downloader.clean_html_content(html_with_wrapper)
        assert result == expected
    
    def test_clean_html_content_handles_complex_wrapper(self):
        """Test mw-parser-output div with additional attributes"""
        html_with_attrs = '<div class="mw-parser-output" dir="ltr" lang="en"><h1>Title</h1><p>Content</p></div>'
        expected = '<h1>Title</h1><p>Content</p>'
        
        result = self.downloader.clean_html_content(html_with_attrs)
        assert result == expected
    
    def test_clean_html_content_both_comments_and_wrapper(self):
        """Test cleaning both comments and wrapper div"""
        html_mixed = '''<div class="mw-parser-output">
<!-- Navigation comment -->
<p>Real content</p>
<!-- End comment -->
<div>More content</div>
</div>'''
        expected = '<p>Real content</p>\n\n<div>More content</div>'
        
        result = self.downloader.clean_html_content(html_mixed)
        assert result == expected
    
    def test_clean_html_content_no_wrapper_div(self):
        """Test content without mw-parser-output wrapper"""
        html_no_wrapper = '<p>Direct content</p><!-- comment --><div>More</div>'
        expected = '<p>Direct content</p><div>More</div>'
        
        result = self.downloader.clean_html_content(html_no_wrapper)
        assert result == expected
    
    def test_clean_html_content_empty_input(self):
        """Test cleaning empty or None input"""
        assert self.downloader.clean_html_content('') == ''
        assert self.downloader.clean_html_content(None) == ''
    
    def test_clean_html_content_adds_h1_title(self):
        """Test that H1 with page title is added"""
        html_content = '<p>Page content here</p>'
        page_title = 'Test Page Title'
        expected = '<h1>Test Page Title</h1>\n<p>Page content here</p>'
        
        result = self.downloader.clean_html_content(html_content, page_title)
        assert result == expected
    
    def test_clean_html_content_escapes_html_in_title(self):
        """Test that HTML characters in title are escaped"""
        html_content = '<p>Content</p>'
        page_title = 'Page <with> "quotes" & ampersands'
        expected = '<h1>Page &lt;with&gt; &quot;quotes&quot; &amp; ampersands</h1>\n<p>Content</p>'
        
        result = self.downloader.clean_html_content(html_content, page_title)
        assert result == expected
    
    def test_clean_html_content_title_only_no_content(self):
        """Test with title but no content"""
        html_content = ''
        page_title = 'Empty Page'
        expected = '<h1>Empty Page</h1>'
        
        result = self.downloader.clean_html_content(html_content, page_title)
        assert result == expected
    
    def test_clean_html_content_no_title_provided(self):
        """Test that content without title works as before"""
        html_content = '<p>Just content</p>'
        expected = '<p>Just content</p>'
        
        result = self.downloader.clean_html_content(html_content)
        assert result == expected
    
    def test_clean_html_content_complete_workflow(self):
        """Test complete workflow with wrapper, comments, and title"""
        html_content = '''<div class="mw-parser-output">
<!-- Start of content -->
<p>This is the main content.</p>
<!-- Table follows -->
<table class="wikitable">
  <tr><td>Data</td></tr>
</table>
</div>'''
        page_title = 'Complete Test Page'
        expected = '''<h1>Complete Test Page</h1>
<p>This is the main content.</p>

<table class="wikitable">
  <tr><td>Data</td></tr>
</table>'''
        
        result = self.downloader.clean_html_content(html_content, page_title)
        assert result == expected


if __name__ == '__main__':
    pytest.main([__file__]) 