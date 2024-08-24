#!/usr/bin/env python3

import io
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTImage, LTFigure
from PIL import Image
import base64
from bs4 import BeautifulSoup

def pdf_to_html(pdf_path, output_html):
    soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
    
    # Add Bootstrap CSS and JS
    bootstrap_css = soup.new_tag('link', rel='stylesheet', href='https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css')
    soup.head.append(bootstrap_css)
    
    bootstrap_js = soup.new_tag('script', src='https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js')
    soup.body.append(bootstrap_js)
    
    # Add custom CSS
    style = soup.new_tag('style')
    style.string = '''
        .pdf-page { margin-bottom: 20px; }
        .pdf-content { position: relative; }
        .pdf-element { margin-bottom: 10px; }
    '''
    soup.head.append(style)
    
    container = soup.new_tag('div', attrs={'class': 'container'})
    soup.body.append(container)
    
    for page_num, page_layout in enumerate(extract_pages(pdf_path), 1):
        page_div = soup.new_tag('div', attrs={'class': 'pdf-page'})
        container.append(page_div)
        
        content_div = soup.new_tag('div', attrs={'class': 'pdf-content'})
        page_div.append(content_div)
        
        def process_element(element):
            if isinstance(element, LTTextBoxHorizontal):
                p_tag = soup.new_tag('p', attrs={'class': 'pdf-element'})
                p_tag.string = element.get_text().strip()
                content_div.append(p_tag)
            elif isinstance(element, LTImage):
                try:
                    image = Image.open(io.BytesIO(element.stream.get_rawdata()))
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    img_tag = soup.new_tag('img', attrs={
                        'src': f"data:image/png;base64,{img_str}",
                        'class': 'pdf-element img-fluid',
                        'alt': 'PDF Image'
                    })
                    content_div.append(img_tag)
                except Exception as e:
                    print(f"Error processing image: {e}")
            elif isinstance(element, LTFigure):
                for child in element:
                    process_element(child)
        
        for element in page_layout:
            process_element(element)
    
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(str(soup))

if __name__ == "__main__":
    import argparse
    import os

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Convert PDF to HTML.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input PDF file')
    parser.add_argument('-o', '--output', help='Path to the output HTML file')

    args = parser.parse_args()

    input_pdf = args.input
    output_html = args.output if args.output else os.path.join(os.path.dirname(input_pdf), 'output.html')

    pdf_to_html(input_pdf, output_html)