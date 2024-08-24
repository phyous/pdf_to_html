#!/usr/bin/env python3

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams, LTTextBox, LTChar
from pdfminer.converter import PDFPageAggregator
from bs4 import BeautifulSoup
from collections import defaultdict

BASE_FONT_SIZE = 13  # You can adjust this value as needed

def pdf_to_html(pdf_path, output_html):
    soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
    
    # Add Bootstrap CSS and JS
    bootstrap_css = soup.new_tag('link', rel='stylesheet', href='https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css')
    soup.head.append(bootstrap_css)
    
    bootstrap_js = soup.new_tag('script', src='https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js')
    soup.body.append(bootstrap_js)
    
    # Update custom CSS
    style = soup.new_tag('style')
    style.string = '''
        body { transition: background-color 0.3s, color 0.3s; }
        .pdf-page { margin-bottom: 20px; }
        .pdf-content { position: relative; }
        .pdf-element { margin-bottom: 10px; }
        #controls { 
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0;
            background-color: #f8f9fa; 
            padding: 15px; 
            z-index: 1000; 
            transition: transform 0.3s ease-in-out;
        }
        #controls.minimized {
            transform: translateY(-100%);
        }
        #divet {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: #007bff;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            z-index: 1001;
            transition: background-color 0.3s;
            border: none;
            font-size: 18px;
        }
        body.dark #divet {
            background-color: #ffffff;
            color: #1a1a1a;
        }
        body.sepia #divet {
            background-color: #5b4636;
            color: #f4ecd8;
        }
    '''
    soup.head.append(style)
    
    # Add font links
    fonts = [
        ('Arial', 'https://fonts.googleapis.com/css2?family=Arial&display=swap'),
        ('Helvetica', 'https://fonts.googleapis.com/css2?family=Helvetica&display=swap'),
        ('Times New Roman', 'https://fonts.googleapis.com/css2?family=Times+New+Roman&display=swap'),
        ('Courier New', 'https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap'),
        ('Verdana', 'https://fonts.googleapis.com/css2?family=Verdana&display=swap'),
        ('Georgia', 'https://fonts.googleapis.com/css2?family=Georgia&display=swap'),
        ('Palatino', 'https://fonts.googleapis.com/css2?family=Palatino&display=swap'),
        ('Garamond', 'https://fonts.googleapis.com/css2?family=EB+Garamond&display=swap'),
        ('Bookman', 'https://fonts.googleapis.com/css2?family=Bookman&display=swap'),
        ('Bookerly', 'https://fonts.googleapis.com/css2?family=Bookerly&display=swap')
    ]
    
    for font_name, font_url in fonts:
        font_link = soup.new_tag('link', rel='stylesheet', href=font_url)
        soup.head.append(font_link)
    
    container = soup.new_tag('div', attrs={'class': 'container'})
    soup.body.append(container)

    # Add divet
    divet = soup.new_tag('button', id='divet')
    divet.string = '🕹️'
    container.append(divet)

    # Add controls
    controls = soup.new_tag('div', id='controls', attrs={'class': 'row mb-3'})
    container.append(controls)

    # Font size selector
    size_col = soup.new_tag('div', attrs={'class': 'col-md-4'})
    size_label = soup.new_tag('label', attrs={'for': 'font-size-selector'})
    size_label.string = 'Size:'
    size_col.append(size_label)
    
    select = soup.new_tag('select', id='font-size-selector', attrs={'class': 'form-control'})
    for size in range(8, 25):
        option = soup.new_tag('option', value=str(size))
        option.string = f'{size}px'
        if size == BASE_FONT_SIZE:
            option['selected'] = 'selected'
        select.append(option)
    size_col.append(select)
    controls.append(size_col)

    # Reading mode selector
    mode_col = soup.new_tag('div', attrs={'class': 'col-md-4'})
    mode_label = soup.new_tag('label', attrs={'for': 'reading-mode-selector'})
    mode_label.string = 'Reading Mode:'
    mode_col.append(mode_label)
    
    mode_select = soup.new_tag('select', id='reading-mode-selector', attrs={'class': 'form-control'})
    for mode in ['Light', 'Dark', 'Sepia']:
        option = soup.new_tag('option', value=mode.lower())
        option.string = mode
        mode_select.append(option)
    mode_col.append(mode_select)
    controls.append(mode_col)

    # Font selector
    font_col = soup.new_tag('div', attrs={'class': 'col-md-4'})
    font_label = soup.new_tag('label', attrs={'for': 'font-selector'})
    font_label.string = 'Font:'
    font_col.append(font_label)
    
    font_select = soup.new_tag('select', id='font-selector', attrs={'class': 'form-control'})
    for font_name, _ in fonts:
        option = soup.new_tag('option', value=font_name)
        option.string = font_name
        font_select.append(option)
    font_col.append(font_select)
    controls.append(font_col)

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

    # Calculate most common font size
    most_common_font_size = max(font_sizes, key=font_sizes.get)
    
    # Create HTML elements
    for text, font_size in text_elements:
        p = soup.new_tag('p', attrs={'class': 'pdf-element', 'data-original-size': f'{font_size:.2f}'})
        p.string = text
        container.append(p)

    # Update JavaScript to handle control changes and scrolling
    script = soup.new_tag('script')
    script.string = '''
    function updateFontSize() {
        var baseFontSize = parseInt(document.getElementById('font-size-selector').value);
        var mostCommonFontSize = %f;
        var elements = document.getElementsByClassName('pdf-element');
        for (var i = 0; i < elements.length; i++) {
            var originalSize = parseFloat(elements[i].getAttribute('data-original-size'));
            var newSize = (originalSize / mostCommonFontSize) * baseFontSize;
            elements[i].style.fontSize = newSize + 'px';
        }
    }

    function updateReadingMode() {
        var mode = document.getElementById('reading-mode-selector').value;
        var body = document.body;
        var divet = document.getElementById('divet');
        switch(mode) {
            case 'light':
                body.style.backgroundColor = '#ffffff';
                body.style.color = '#000000';
                body.className = 'light';
                divet.style.backgroundColor = '#007bff';
                divet.style.color = '#ffffff';
                break;
            case 'dark':
                body.style.backgroundColor = '#1a1a1a';
                body.style.color = '#ffffff';
                body.className = 'dark';
                divet.style.backgroundColor = '#ffffff';
                divet.style.color = '#1a1a1a';
                break;
            case 'sepia':
                body.style.backgroundColor = '#f4ecd8';
                body.style.color = '#5b4636';
                body.className = 'sepia';
                divet.style.backgroundColor = '#5b4636';
                divet.style.color = '#f4ecd8';
                break;
        }
    }

    function updateFont() {
        var font = document.getElementById('font-selector').value;
        document.body.style.fontFamily = font + ', sans-serif';
    }

    function toggleControls() {
        var controls = document.getElementById('controls');
        controls.classList.toggle('minimized');
    }

    document.getElementById('font-size-selector').addEventListener('change', updateFontSize);
    document.getElementById('reading-mode-selector').addEventListener('change', updateReadingMode);
    document.getElementById('font-selector').addEventListener('change', updateFont);
    document.getElementById('divet').addEventListener('click', toggleControls);

    // Initial setup
    updateFontSize();
    updateReadingMode();
    updateFont();
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