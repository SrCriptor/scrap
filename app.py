import os
import logging
from flask import Flask, render_template, request, flash, jsonify
from media_scraper import MediaScraper
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize media scraper
scraper = MediaScraper()

@app.route('/')
def index():
    """Página principal com formulário para inserir URL"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape_media():
    """Endpoint para fazer scraping de mídia de uma URL"""
    try:
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('Por favor, insira uma URL válida.', 'error')
            return render_template('index.html')
        
        # Validar URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            flash('URL inválida. Certifique-se de incluir http:// ou https://', 'error')
            return render_template('index.html')
        
        # Fazer scraping
        app.logger.info(f"Iniciando scraping da URL: {url}")
        media_data = scraper.scrape_media(url)
        
        if not media_data['images'] and not media_data['videos']:
            flash('Nenhuma mídia encontrada nesta página.', 'warning')
            return render_template('index.html')
        
        app.logger.info(f"Scraping concluído. Imagens: {len(media_data['images'])}, Vídeos: {len(media_data['videos'])}")
        
        return render_template('results.html', 
                             media_data=media_data, 
                             original_url=url)
    
    except Exception as e:
        app.logger.error(f"Erro durante o scraping: {str(e)}")
        flash(f'Erro ao processar a página: {str(e)}', 'error')
        return render_template('index.html')

@app.route('/validate_url', methods=['POST'])
def validate_url():
    """Endpoint AJAX para validação de URL em tempo real"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'valid': False, 'message': 'URL não pode estar vazia'})
        
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return jsonify({'valid': False, 'message': 'Formato de URL inválido'})
        
        return jsonify({'valid': True, 'message': 'URL válida'})
    
    except Exception as e:
        return jsonify({'valid': False, 'message': 'Erro na validação'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
