from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import os
from model import assistant

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация сервера
POD_ID = "egkjwlv8eg71du"
PORT = 1000
HOST = '0.0.0.0'
BASE_URL = f"https://{POD_ID}-{PORT}.proxy.runpod.net"

# Пример базы дизайн-макетов
DESIGN_TEMPLATES = {
    'landing': {
        'name': 'Modern Landing Page',
        'description': 'Clean and modern landing page with hero section',
        'components': ['hero', 'features', 'testimonials'],
        'style': 'modern',
        'preview_url': 'https://images.unsplash.com/photo-1551434678-e076c223a692?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80'
    },
    'dashboard': {
        'name': 'Admin Dashboard',
        'description': 'Professional admin interface with data visualization',
        'components': ['sidebar', 'charts', 'tables'],
        'style': 'professional',
        'preview_url': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80'
    },
    'portfolio': {
        'name': 'Creative Portfolio',
        'description': 'Artistic portfolio layout with gallery',
        'components': ['gallery', 'about', 'contact'],
        'style': 'creative',
        'preview_url': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80'
    }
}

def analyze_page_structure(soup):
    """Анализирует структуру страницы и определяет тип контента"""
    structure = {
        'has_hero': bool(soup.find('section', class_=lambda x: x and ('hero' in x or 'banner' in x))),
        'has_gallery': bool(soup.find('div', class_=lambda x: x and ('gallery' in x or 'portfolio' in x))),
        'has_forms': bool(soup.find('form')),
        'has_tables': bool(soup.find('table')),
        'has_cards': bool(soup.find('div', class_=lambda x: x and 'card' in x)),
        'style': 'modern'  # По умолчанию
    }
    
    # Определяем стиль по используемым классам
    if soup.find(class_=lambda x: x and ('bootstrap' in x or 'material' in x)):
        structure['style'] = 'professional'
    elif soup.find(class_=lambda x: x and ('creative' in x or 'artistic' in x)):
        structure['style'] = 'creative'
        
    return structure

def suggest_templates(structure):
    """Подбирает подходящие шаблоны на основе структуры страницы"""
    suggestions = []
    
    for template_id, template in DESIGN_TEMPLATES.items():
        score = 0
        
        # Проверяем соответствие компонентов
        if structure['has_hero'] and 'hero' in template['components']:
            score += 2
        if structure['has_gallery'] and 'gallery' in template['components']:
            score += 2
        if structure['has_tables'] and 'tables' in template['components']:
            score += 2
            
        # Проверяем соответствие стиля
        if structure['style'] == template['style']:
            score += 1
            
        if score > 0:
            suggestions.append({
                **template,
                'id': template_id,
                'score': score
            })
    
    # Сортируем по релевантности
    return sorted(suggestions, key=lambda x: x['score'], reverse=True)

@app.route('/')
def index():
    try:
        logger.debug("Обработка запроса к главной странице")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Ошибка при обработке главной страницы: {str(e)}")
        return "Internal Server Error", 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        logger.debug(f"Запрос статического файла: {filename}")
        return send_from_directory('static', filename)
    except Exception as e:
        logger.error(f"Ошибка при обслуживании статического файла {filename}: {str(e)}")
        return "File not found", 404

@app.route('/parse', methods=['POST'])
def parse_website():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Add https:// if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Fetch the website
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Анализируем структуру страницы
        structure = analyze_page_structure(soup)
        
        # Подбираем подходящие шаблоны
        suggested_templates = suggest_templates(structure)

        # Extract information
        result = {
            'title': soup.title.string if soup.title else 'No title',
            'meta': [{'name': meta.get('name'), 'content': meta.get('content')} 
                    for meta in soup.find_all('meta')],
            'links': [{'href': link.get('href'), 'text': link.text} 
                     for link in soup.find_all('a')],
            'scripts': [script.get('src') for script in soup.find_all('script') 
                       if script.get('src')],
            'styles': [style.get('href') for style in soup.find_all('link', rel='stylesheet') 
                      if style.get('href')],
            'images': [img.get('src') for img in soup.find_all('img') 
                      if img.get('src')],
            'html': response.text,  # Add the full HTML source
            'js': '\n'.join([script.string for script in soup.find_all('script') 
                           if script.string and not script.get('src')]),  # Add inline JavaScript
            'css': '\n'.join([style.string for style in soup.find_all('style') 
                            if style.string]),  # Add inline CSS
            'structure': structure,
            'suggested_templates': suggested_templates
        }

        # Convert relative image URLs to absolute URLs
        base_url = '/'.join(url.split('/')[:3])  # Get the base URL (e.g., https://example.com)
        result['images'] = [
            img_url if img_url.startswith(('http://', 'https://')) 
            else f"{base_url}{img_url if img_url.startswith('/') else '/' + img_url}"
            for img_url in result['images']
        ]

        # Fetch external CSS files
        css_content = []
        for style_url in result['styles']:
            try:
                if style_url.startswith('http'):
                    css_response = requests.get(style_url)
                else:
                    # Handle relative URLs
                    base_url = '/'.join(url.split('/')[:3])
                    css_response = requests.get(f"{base_url}{style_url}")
                css_content.append(css_response.text)
            except:
                continue

        if css_content:
            result['css'] += '\n\n/* External CSS Files */\n\n' + '\n\n'.join(css_content)

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.json
        message = data.get('message')
        current_code = data.get('currentCode', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        try:
            # Подготавливаем контекст для модели
            context = {
                'html': current_code.get('html', ''),
                'css': current_code.get('css', ''),
                'js': current_code.get('js', ''),
                'structure': current_code.get('structure', {}),
                'meta': current_code.get('meta', []),
                'links': current_code.get('links', []),
                'scripts': current_code.get('scripts', []),
                'styles': current_code.get('styles', []),
                'images': current_code.get('images', [])
            }

            # Используем локальную модель для генерации ответа
            response = assistant.generate_response(message, context)
            
            # Если модель предложила изменения, применяем их
            if response.get('suggestedChanges'):
                # Здесь можно добавить логику применения изменений
                # Например, обновление HTML, CSS или JS
                pass

            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                'message': f"Произошла ошибка при обработке запроса: {str(e)}",
                'suggestedChanges': None
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def apply_template(html, css, template_id):
    """Применяет выбранный шаблон к HTML и CSS"""
    template = DESIGN_TEMPLATES.get(template_id)
    if not template:
        return html, css

    soup = BeautifulSoup(html, 'html.parser')
    
    # Применяем стили в зависимости от шаблона
    if template_id == 'landing':
        # Добавляем современные стили
        css += """
        /* Modern Landing Page Styles */
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            padding: 4rem 2rem;
        }
        """
    elif template_id == 'dashboard':
        # Добавляем стили для дашборда
        css += """
        /* Dashboard Styles */
        body {
            font-family: 'Roboto', sans-serif;
            background: #f5f6fa;
        }
        .sidebar {
            background: #2c3e50;
            color: white;
            padding: 1rem;
            min-height: 100vh;
        }
        .content {
            padding: 2rem;
        }
        """
    elif template_id == 'portfolio':
        # Добавляем стили для портфолио
        css += """
        /* Portfolio Styles */
        body {
            font-family: 'Playfair Display', serif;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            padding: 2rem;
        }
        """

    return str(soup), css

@app.route('/apply_template', methods=['POST'])
def apply_template_route():
    try:
        data = request.json
        html = data.get('html')
        css = data.get('css')
        template_id = data.get('template_id')

        if not all([html, css, template_id]):
            return jsonify({'error': 'Missing required parameters'}), 400

        modified_html, modified_css = apply_template(html, css, template_id)

        return jsonify({
            'html': modified_html,
            'css': modified_css,
            'message': 'Template applied successfully'
        })

    except Exception as e:
        logger.error(f"Error applying template: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Запуск сервера на {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True) 
 