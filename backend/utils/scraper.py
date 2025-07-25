import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin, urlparse
from config.settings import settings
import time


class NovelScraper:
    """Web scraper for novels from various sources."""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_novel(self, url: str, language: str = "en") -> Dict:
        """Scrape a novel from a URL."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        
        try:
            # Determine scraping strategy based on domain
            domain = urlparse(url).netloc.lower()
            
            if 'wuxiaworld' in domain:
                return await self._scrape_wuxiaworld(url)
            elif 'novelupdates' in domain:
                return await self._scrape_novelupdates(url)
            elif 'webnovel' in domain:
                return await self._scrape_webnovel(url)
            elif 'qidian' in domain:
                return await self._scrape_qidian(url)
            else:
                return await self._scrape_generic(url, language)
        
        except Exception as e:
            raise Exception(f"Failed to scrape novel: {str(e)}")
    
    async def _scrape_generic(self, url: str, language: str) -> Dict:
        """Generic scraping method for unknown sites."""
        async with self.session.get(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: Failed to fetch {url}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try to extract basic information
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            description = self._extract_description(soup)
            
            # Try to find chapter links
            chapter_links = self._find_chapter_links(soup, url)
            
            # Scrape chapters
            chapters = []
            for i, chapter_url in enumerate(chapter_links[:10]):  # Limit to 10 chapters for demo
                try:
                    chapter_content = await self._scrape_chapter(chapter_url)
                    chapters.append({
                        "title": f"Chapter {i+1}",
                        "content": chapter_content
                    })
                    await asyncio.sleep(settings.request_delay)  # Rate limiting
                except Exception as e:
                    print(f"Failed to scrape chapter {chapter_url}: {e}")
                    continue
            
            return {
                "title": title,
                "author": author,
                "description": description,
                "chapters": chapters,
                "source_url": url
            }
    
    async def _scrape_wuxiaworld(self, url: str) -> Dict:
        """Scrape from WuxiaWorld."""
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # WuxiaWorld specific selectors
            title_elem = soup.find('h1', class_='novel-title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            author_elem = soup.find('span', class_='author') or soup.find('a', href=re.compile(r'/author/'))
            author = author_elem.get_text().strip() if author_elem else None
            
            desc_elem = soup.find('div', class_='synopsis') or soup.find('div', class_='description')
            description = desc_elem.get_text().strip() if desc_elem else None
            
            # Find chapter list
            chapter_links = []
            chapter_list = soup.find('div', class_='chapter-list') or soup.find('ul', class_='chapters')
            if chapter_list:
                for link in chapter_list.find_all('a', href=True):
                    chapter_url = urljoin(url, link['href'])
                    chapter_links.append(chapter_url)
            
            chapters = await self._scrape_chapters(chapter_links[:5])  # Limit for demo
            
            return {
                "title": title,
                "author": author,
                "description": description,
                "chapters": chapters,
                "source_url": url
            }
    
    async def _scrape_webnovel(self, url: str) -> Dict:
        """Scrape from WebNovel."""
        # WebNovel often requires JavaScript, so this is a simplified version
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # WebNovel structure varies, this is a basic implementation
            return {
                "title": title,
                "author": None,
                "description": None,
                "chapters": [],
                "source_url": url
            }
    
    async def _scrape_qidian(self, url: str) -> Dict:
        """Scrape from Qidian (Chinese novels)."""
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Qidian specific selectors (simplified)
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            return {
                "title": title,
                "author": None,
                "description": None,
                "chapters": [],
                "source_url": url
            }
    
    async def _scrape_chapters(self, chapter_urls: List[str]) -> List[Dict]:
        """Scrape multiple chapters."""
        chapters = []
        
        for i, chapter_url in enumerate(chapter_urls):
            try:
                content = await self._scrape_chapter(chapter_url)
                chapters.append({
                    "title": f"Chapter {i+1}",
                    "content": content
                })
                await asyncio.sleep(settings.request_delay)
            except Exception as e:
                print(f"Failed to scrape chapter {chapter_url}: {e}")
                continue
        
        return chapters
    
    async def _scrape_chapter(self, url: str) -> str:
        """Scrape a single chapter."""
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Common content selectors
            content_selectors = [
                'div.chapter-content',
                'div.content',
                'div.text',
                'div.chapter-text',
                'article',
                'main',
                '.entry-content'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return content or "No content found"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from soup."""
        # Try various title selectors
        title_selectors = ['h1', 'h2', '.title', '.novel-title', 'title']
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text().strip():
                return elem.get_text().strip()
        
        return "Unknown Title"
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from soup."""
        author_selectors = ['.author', '.writer', '[class*="author"]', 'a[href*="author"]']
        
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text().strip():
                return elem.get_text().strip()
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from soup."""
        desc_selectors = ['.description', '.synopsis', '.summary', '.intro']
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text().strip():
                return elem.get_text().strip()
        
        return None
    
    def _find_chapter_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find chapter links in the page."""
        chapter_links = []
        
        # Look for links that might be chapters
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()
            
            # Check if link text suggests it's a chapter
            if any(keyword in text for keyword in ['chapter', '章', '話', 'ch.']):
                full_url = urljoin(base_url, href)
                chapter_links.append(full_url)
        
        return chapter_links[:50]  # Limit to 50 chapters
