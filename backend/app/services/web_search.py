import asyncio
import logging
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import httpx
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class WebSearchService:
    """Service for searching web information about stores and places"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = None
    
    async def get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=10.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def search_store_info(self, store_name: str, location: str = "") -> Optional[Dict[str, Any]]:
        """Search for information about a specific store or place"""
        try:
            # Construct search query
            query = f"{store_name}"
            if location:
                query += f" {location}"
            
            logger.info(f"Starting web search for: {query}")
            
            # Search using DuckDuckGo
            search_results = await self._ddg_search(query)
            
            if not search_results:
                logger.warning(f"No search results found for: {query}")
                return None
            
            logger.info(f"Processing {len(search_results)} search results for: {store_name}")
            
            # Get detailed information from the top results
            store_info = await self._extract_store_details(search_results[:3])
            
            result = {
                "store_name": store_name,
                "search_query": query,
                "info": store_info,
                "search_results_count": len(search_results)
            }
            
            logger.info(f"Successfully extracted info for {store_name}: {list(store_info.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching for {store_name}: {str(e)}", exc_info=True)
            return None
    
    async def _ddg_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform DuckDuckGo search with timeout and retry"""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"DuckDuckGo search attempt {attempt + 1}/{max_retries + 1} for: {query}")
                
                # Run search in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                # Add timeout to prevent hanging
                results = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: list(self.ddgs.text(query, max_results=max_results))
                    ),
                    timeout=15.0  # 15 second timeout
                )
                
                logger.info(f"Found {len(results)} search results for: {query}")
                return results
                
            except asyncio.TimeoutError:
                logger.warning(f"DuckDuckGo search timeout for: {query} (attempt {attempt + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(1)  # Wait before retry
                    continue
                else:
                    logger.error(f"DuckDuckGo search failed after {max_retries + 1} attempts (timeout)")
                    return []
                    
            except Exception as e:
                logger.warning(f"DuckDuckGo search error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(1)  # Wait before retry
                    continue
                else:
                    logger.error(f"DuckDuckGo search failed after {max_retries + 1} attempts: {str(e)}")
                    return []
    
    async def _extract_store_details(self, search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract relevant store information from search results"""
        try:
            info = {
                "description": "",
                "location": "",
                "hours": "",
                "price_range": "",
                "rating": "",
                "specialties": [],
                "atmosphere": "",
                "contact": "",
                "website": ""
            }
            
            session = await self.get_session()
            
            for result in search_results:
                try:
                    url = result.get('href', '')
                    title = result.get('title', '')
                    snippet = result.get('body', '')
                    
                    # Extract information from snippet
                    self._extract_from_snippet(snippet, info)
                    
                    # Try to get more details from the webpage
                    if url and ('tabelog' in url or 'gurunavi' in url or 'retty' in url or 'google' in url):
                        page_info = await self._scrape_restaurant_page(session, url)
                        if page_info:
                            self._merge_info(info, page_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing search result: {str(e)}")
                    continue
            
            # Clean up and format information
            self._clean_info(info)
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting store details: {str(e)}")
            return {}
    
    def _extract_from_snippet(self, snippet: str, info: Dict[str, Any]):
        """Extract information from search result snippet"""
        if not snippet:
            return
        
        # Extract price information
        price_patterns = [
            r'[￥¥]\s*(\d+[,\d]*)',
            r'(\d+[,\d]*)\s*円',
            r'予算[：:]\s*([^、。\n]+)',
            r'料金[：:]\s*([^、。\n]+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, snippet)
            if match and not info["price_range"]:
                info["price_range"] = match.group(0)
                break
        
        # Extract rating
        rating_patterns = [
            r'評価[：:]\s*([0-9.]+)',
            r'★\s*([0-9.]+)',
            r'([0-9.]+)\s*点',
            r'([0-9.]+)/5'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, snippet)
            if match and not info["rating"]:
                info["rating"] = match.group(1)
                break
        
        # Extract hours
        hour_patterns = [
            r'営業時間[：:]\s*([^、。\n]+)',
            r'時間[：:]\s*([^、。\n]+)',
            r'(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})'
        ]
        
        for pattern in hour_patterns:
            match = re.search(pattern, snippet)
            if match and not info["hours"]:
                info["hours"] = match.group(0)
                break
        
        # Extract location
        location_patterns = [
            r'住所[：:]\s*([^、。\n]+)',
            r'所在地[：:]\s*([^、。\n]+)',
            r'アクセス[：:]\s*([^、。\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, snippet)
            if match and not info["location"]:
                info["location"] = match.group(1)
                break
        
        # Store description if not already set
        if not info["description"] and len(snippet) > 20:
            info["description"] = snippet[:200] + "..." if len(snippet) > 200 else snippet
    
    async def _scrape_restaurant_page(self, session: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
        """Scrape additional information from restaurant website"""
        try:
            response = await session.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_info = {}
            
            # Extract title
            title = soup.find('title')
            if title:
                page_info["title"] = title.get_text().strip()
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                page_info["meta_description"] = meta_desc.get('content').strip()
            
            return page_info
            
        except Exception as e:
            logger.warning(f"Error scraping {url}: {str(e)}")
            return None
    
    def _merge_info(self, main_info: Dict[str, Any], additional_info: Dict[str, Any]):
        """Merge additional information into main info"""
        for key, value in additional_info.items():
            if value and not main_info.get(key):
                main_info[key] = value
    
    def _clean_info(self, info: Dict[str, Any]):
        """Clean and format extracted information"""
        # Remove empty strings and clean up text
        for key, value in info.items():
            if isinstance(value, str):
                info[key] = value.strip()
                # Remove excessive whitespace
                info[key] = re.sub(r'\s+', ' ', info[key])
    
    async def detect_store_names(self, options: List[str]) -> List[str]:
        """Detect which options might be store names that need web search"""
        store_indicators = [
            '店', '屋', 'レストラン', 'カフェ', 'cafe', '食堂', '居酒屋',
            'バー', 'bar', 'ホテル', '旅館', 'リゾート', '温泉',
            'A', 'B', 'C', 'D', 'E'  # Common store suffix patterns
        ]
        
        # Common Japanese chain stores and restaurant names
        known_chains = [
            'マクドナルド', 'マック', 'McDonald', 'スターバックス', 'スタバ', 'Starbucks',
            'サイゼリヤ', 'サイゼ', 'ガスト', 'すき家', 'なか卯', '松屋', '吉野家',
            'ケンタッキー', 'KFC', 'モスバーガー', 'モス', 'ファミマ', 'セブン',
            'ローソン', 'イオン', 'コメダ', 'ドトール', 'タリーズ', 'ココス',
            'デニーズ', 'ジョナサン', 'バーミヤン', 'ロイヤルホスト', 'びっくりドンキー',
            '丸亀製麺', 'はなまるうどん', 'リンガーハット', '王将', '餃子の王将',
            'ラーメン二郎', '一蘭', '一風堂', 'くら寿司', 'スシロー', 'はま寿司',
            '回転寿司', '焼肉きんぐ', '牛角', 'ステーキガスト', 'いきなりステーキ'
        ]
        
        detected_stores = []
        
        for option in options:
            option_lower = option.lower()
            detected = False
            
            # Check for known chain stores first
            for chain in known_chains:
                if chain.lower() in option_lower or chain in option:
                    detected_stores.append(option)
                    detected = True
                    logger.info(f"Detected known chain: {option} (matched: {chain})")
                    break
            
            if not detected:
                # Check if option contains store indicators
                if any(indicator in option for indicator in store_indicators):
                    detected_stores.append(option)
                    detected = True
                    logger.info(f"Detected store by indicator: {option}")
                
                # Check if option looks like a proper noun (starts with capital or has specific patterns)
                elif (len(option) > 2 and 
                      (option[0].isupper() or 
                       any(char in option for char in ['亭', '庵', '館', '苑', '園']))):
                    detected_stores.append(option)
                    detected = True
                    logger.info(f"Detected store by pattern: {option}")
        
        logger.info(f"Total detected stores: {len(detected_stores)} from options: {options}")
        return list(set(detected_stores))  # Remove duplicates
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None

# Global instance
web_search_service = WebSearchService()