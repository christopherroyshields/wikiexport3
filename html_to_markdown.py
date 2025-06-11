#!/usr/bin/env python3
"""
HTML to Markdown converter for wiki pages.
Reads HTML files and converts them to Markdown format.
"""

import os
import argparse
import glob
import re
from pathlib import Path
from typing import List, Optional
import markdownify


class HTMLToMarkdownConverter:
    def __init__(self, input_dir: str = "wiki_pages", output_dir: str = "markdown_pages"):
        """
        Initialize the HTML to Markdown converter.
        
        Args:
            input_dir: Directory containing HTML files to convert
            output_dir: Directory to save converted Markdown files
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def find_html_files(self) -> List[str]:
        """
        Find all HTML files in the input directory.
        
        Returns:
            List of HTML file paths
        """
        pattern = os.path.join(self.input_dir, "*.html")
        html_files = glob.glob(pattern)
        return sorted(html_files)
    
    def convert_html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Converted Markdown content
        """
        # Configure markdownify for better conversion
        markdown_content = markdownify.markdownify(
            html_content,
            heading_style="ATX",  # Use # for headings instead of underlines
            bullets="-",          # Use - for bullet points
            strip=['script', 'style', 'a']  # Remove script and style tags
        )
        
        # Clean up extra whitespace
        lines = markdown_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            cleaned_lines.append(line)
        
        # Join lines and remove excessive blank lines
        markdown_content = '\n'.join(cleaned_lines)
        
        # Replace multiple consecutive newlines with maximum of 2
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        return markdown_content.strip()
    
    def get_output_filename(self, html_filepath: str) -> str:
        """
        Generate output filename for Markdown file.
        
        Args:
            html_filepath: Path to the HTML file
            
        Returns:
            Path to the output Markdown file
        """
        # Get the base filename without extension
        base_name = os.path.splitext(os.path.basename(html_filepath))[0]
        
        # Create Markdown filename
        markdown_filename = f"{base_name}.md"
        
        # Ensure unique filename if file already exists
        # counter = 1
        # while os.path.exists(os.path.join(self.output_dir, markdown_filename)):
        #     markdown_filename = f"{base_name}_{counter}.md"
        #     counter += 1
        
        return os.path.join(self.output_dir, markdown_filename)
    
    def convert_file(self, html_filepath: str) -> Optional[str]:
        """
        Convert a single HTML file to Markdown.
        
        Args:
            html_filepath: Path to the HTML file to convert
            
        Returns:
            Path to the converted Markdown file, or None if conversion failed
        """
        try:
            # Read HTML file
            with open(html_filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Convert to Markdown
            markdown_content = self.convert_html_to_markdown(html_content)
            
            # Generate output filename
            output_filepath = self.get_output_filename(html_filepath)
            
            # Save Markdown file
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return output_filepath
            
        except Exception as e:
            print(f"Error converting {html_filepath}: {e}")
            return None
    
    def convert_all_files(self) -> None:
        """
        Convert all HTML files in the input directory to Markdown.
        """
        html_files = self.find_html_files()
        
        if not html_files:
            print(f"No HTML files found in {self.input_dir}")
            return
        
        print(f"Found {len(html_files)} HTML files to convert")
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        converted = 0
        failed = 0
        skipped = 0
        
        for i, html_file in enumerate(html_files, 1):
            filename = os.path.basename(html_file)
            print(f"[{i}/{len(html_files)}] Converting: {filename}")
            
            # Check if file is empty before attempting conversion
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                if not html_content.strip():
                    print(f"  Skipping empty file")
                    skipped += 1
                    continue
                
                # Check if file only contains an H1 tag
                cleaned_content = re.sub(r'\s+', ' ', html_content.strip())
                h1_only_pattern = r'^<h1[^>]*>.*?</h1>$'
                if re.match(h1_only_pattern, cleaned_content, re.IGNORECASE | re.DOTALL):
                    print(f"  Skipping file with only H1 tag")
                    skipped += 1
                    continue
                    
            except Exception as e:
                print(f"  Error reading file: {e}")
                failed += 1
                continue
            
            output_file = self.convert_file(html_file)
            
            if output_file:
                print(f"  Saved to: {output_file}")
                converted += 1
            else:
                print(f"  Failed to convert")
                failed += 1
        
        print(f"\nConversion complete!")
        print(f"Successfully converted: {converted} files")
        print(f"Skipped empty files: {skipped} files")
        print(f"Failed: {failed} files")


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML wiki pages to Markdown format"
    )
    parser.add_argument(
        '-i', '--input',
        default='wiki_pages',
        help='Input directory containing HTML files (default: wiki_pages)'
    )
    parser.add_argument(
        '-o', '--output',
        default='markdown_pages',
        help='Output directory for Markdown files (default: markdown_pages)'
    )
    parser.add_argument(
        '-f', '--file',
        help='Convert a specific HTML file instead of entire directory'
    )
    
    args = parser.parse_args()
    
    converter = HTMLToMarkdownConverter(args.input, args.output)
    
    if args.file:
        # Convert single file
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            return
        
        # Check if file is empty
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            if not html_content.strip():
                print(f"File {args.file} is empty - skipping conversion")
                return
                
            # Check if file only contains an H1 tag
            cleaned_content = re.sub(r'\s+', ' ', html_content.strip())
            h1_only_pattern = r'^<h1[^>]*>.*?</h1>$'
            if re.match(h1_only_pattern, cleaned_content, re.IGNORECASE | re.DOTALL):
                print(f"File {args.file} only contains an H1 tag - skipping conversion")
                return
                
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return
        
        print(f"Converting single file: {args.file}")
        output_file = converter.convert_file(args.file)
        
        if output_file:
            print(f"Successfully converted to: {output_file}")
        else:
            print("Conversion failed")
    else:
        # Convert all files in directory
        converter.convert_all_files()


if __name__ == '__main__':
    main() 