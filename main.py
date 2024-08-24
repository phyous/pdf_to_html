#!/usr/bin/env python3

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams, LTTextBox, LTChar
from pdfminer.converter import PDFPageAggregator
from bs4 import BeautifulSoup
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_FONT_SIZE = 16  # You can adjust this value as needed

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

    font_sizes = defaultdict(int)
    text_elements = []

    with open(pdf_path, 'rb') as file:
        parser = PDFParser(file)
        document = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            for element in layout:
                if isinstance(element, LTTextBox):
                    text = element.get_text().strip()
                    if text:
                        font_size = None
                        for obj in element._objs:
                            for char in obj._objs:
                                if isinstance(char, LTChar):
                                    font_size = char.size
                                    break
                            if font_size:
                                break
                        
                        if font_size:
                            font_sizes[font_size] += len(text)  # Weight by character count
                            text_elements.append((text, font_size))
                            logging.info(f"Text: '{text[:30]}...', Font Size: {font_size:.2f}")
                        else:
                            logging.warning(f"No font size detected for text: '{text[:30]}...'")

    # Calculate most common font size
    most_common_font_size = max(font_sizes, key=font_sizes.get)
    
    # Add font size selector
    select = soup.new_tag('select', id='font-size-selector', **{'class': 'form-control mb-3'})
    for size in range(8, 25):
        option = soup.new_tag('option', value=str(size))
        option.string = f'{size}px'
        if size == BASE_FONT_SIZE:
            option['selected'] = 'selected'
        select.append(option)
    container.append(select)

    # Create HTML elements
    for text, font_size in text_elements:
        p = soup.new_tag('p', attrs={'class': 'pdf-element', 'data-original-size': f'{font_size:.2f}'})
        p.string = text
        container.append(p)

    # Add JavaScript to handle font size changes
    script = soup.new_tag('script')
    script.string = '''
    document.getElementById('font-size-selector').addEventListener('change', function() {
        var baseFontSize = parseInt(this.value);
        var mostCommonFontSize = %f;
        var elements = document.getElementsByClassName('pdf-element');
        for (var i = 0; i < elements.length; i++) {
            var originalSize = parseFloat(elements[i].getAttribute('data-original-size'));
            var newSize = (originalSize / mostCommonFontSize) * baseFontSize;
            elements[i].style.fontSize = newSize + 'px';
        }
    });
    
    // Initial setup
    var event = new Event('change');
    document.getElementById('font-size-selector').dispatchEvent(event);
    ''' % most_common_font_size
    soup.body.append(script)

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