import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

class MediaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Extensões de mídia suportadas
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}
        self.video_extensions = {'.mp4', '.webm', '.ogg', '.flv', '.avi', '.mov', '.wmv', '.mkv'}
        
        # Padrões regex para encontrar URLs de mídia
        self.media_patterns = [
            r'https?://[^\s"\'<>]+\.(?:mp4|webm|ogg|png|jpg|jpeg|gif|webp|bmp|flv|avi|mov|wmv|mkv)',
            r'https?://[^\s"\'<>]*(?:youtube\.com/watch\?v=|youtu\.be/|vimeo\.com/)[^\s"\'<>]*',
            r'https?://[^\s"\'<>]*(?:instagram\.com/p/|twitter\.com/[^/]+/status/)[^\s"\'<>]*'
        ]

    def scrape_media(self, url):
        """
        Faz scraping de uma URL e extrai todos os links de mídia
        """
        try:
            # Fazer requisição para a página
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair mídia de diferentes fontes
            images = self._extract_images(soup, url)
            videos = self._extract_videos(soup, url)
            
            # Extrair mídia adicional usando regex no HTML
            html_content = response.text
            regex_media = self._extract_with_regex(html_content, url)
            
            # Combinar e remover duplicatas
            all_images = list(set(images + regex_media['images']))
            all_videos = list(set(videos + regex_media['videos']))
            
            # Filtrar e validar URLs
            valid_images = self._validate_media_urls(all_images)
            valid_videos = self._validate_media_urls(all_videos)
            
            return {
                'images': valid_images,
                'videos': valid_videos,
                'total_media': len(valid_images) + len(valid_videos)
            }
            
        except requests.RequestException as e:
            logging.error(f"Erro na requisição: {e}")
            raise Exception(f"Não foi possível acessar a página: {str(e)}")
        except Exception as e:
            logging.error(f"Erro no scraping: {e}")
            raise Exception(f"Erro ao processar a página: {str(e)}")

    def _extract_images(self, soup, base_url):
        """Extrai imagens de tags HTML"""
        images = []
        
        # Tags img
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                full_url = urljoin(base_url, src)
                if self._is_image_url(full_url):
                    images.append(full_url)
        
        # Tags picture e source
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                srcset = source.get('srcset')
                if srcset:
                    # Extrair URLs do srcset
                    urls = re.findall(r'(https?://[^\s,]+)', srcset)
                    for url in urls:
                        full_url = urljoin(base_url, url)
                        if self._is_image_url(full_url):
                            images.append(full_url)
        
        # Meta tags (Open Graph, Twitter Cards)
        for meta in soup.find_all('meta'):
            property_val = meta.get('property') or meta.get('name')
            if property_val in ['og:image', 'twitter:image', 'twitter:image:src']:
                content = meta.get('content')
                if content:
                    full_url = urljoin(base_url, content)
                    if self._is_image_url(full_url):
                        images.append(full_url)
        
        return images

    def _extract_videos(self, soup, base_url):
        """Extrai vídeos de tags HTML"""
        videos = []
        
        # Tags video
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                full_url = urljoin(base_url, src)
                if self._is_video_url(full_url):
                    videos.append(full_url)
            
            # Sources dentro do video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if self._is_video_url(full_url):
                        videos.append(full_url)
        
        # iframes (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ('youtube.com' in src or 'vimeo.com' in src or 'dailymotion.com' in src):
                full_url = urljoin(base_url, src)
                videos.append(full_url)
        
        # Meta tags para vídeos
        for meta in soup.find_all('meta'):
            property_val = meta.get('property') or meta.get('name')
            if property_val in ['og:video', 'og:video:url', 'twitter:player']:
                content = meta.get('content')
                if content:
                    full_url = urljoin(base_url, content)
                    videos.append(full_url)
        
        return videos

    def _extract_with_regex(self, html_content, base_url):
        """Extrai mídia usando regex no conteúdo HTML"""
        images = []
        videos = []
        
        for pattern in self.media_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                full_url = urljoin(base_url, match)
                if self._is_image_url(full_url):
                    images.append(full_url)
                elif self._is_video_url(full_url) or 'youtube.com' in full_url or 'vimeo.com' in full_url:
                    videos.append(full_url)
        
        return {'images': images, 'videos': videos}

    def _is_image_url(self, url):
        """Verifica se a URL é de uma imagem"""
        try:
            parsed = urlparse(url.lower())
            path = parsed.path
            return any(path.endswith(ext) for ext in self.image_extensions)
        except:
            return False

    def _is_video_url(self, url):
        """Verifica se a URL é de um vídeo"""
        try:
            parsed = urlparse(url.lower())
            path = parsed.path
            return any(path.endswith(ext) for ext in self.video_extensions)
        except:
            return False

    def _validate_media_urls(self, urls):
        """Valida e filtra URLs de mídia"""
        valid_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme in ['http', 'https'] and parsed.netloc:
                    # Remover parâmetros desnecessários para alguns tipos de URL
                    clean_url = url.split('?')[0] if not ('youtube.com' in url or 'vimeo.com' in url) else url
                    valid_urls.append(clean_url)
            except:
                continue
        
        return valid_urls
