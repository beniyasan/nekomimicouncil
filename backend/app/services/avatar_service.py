import os
import logging
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

class AvatarService:
    """Service for managing avatar images"""
    
    def __init__(self):
        self.icon_dir = Path(__file__).parent.parent.parent.parent / "data" / "icon"
        self.resized_dir = self.icon_dir / "resized"
        self.avatar_size = (48, 48)  # 48x48 pixels for avatars
        
        # Create resized directory if it doesn't exist
        self.resized_dir.mkdir(exist_ok=True)
        
        # Persona ID to icon filename mapping
        self.persona_icon_map = {
            "gourmet": "maria.png",        # 美食家マリア
            "budget": "takesi.png",        # 節約家タケシ  
            "health": "yuri.png",          # ヘルシー志向のユリ
            "trendy": "ai.png",            # トレンド好きアイ
            "traditional": "ichiro.png",   # 伝統派のイチロウ
            "busy": "sato.png",            # 忙しいサラリーマン サトウ
            "family": "hanako.png",        # ファミリー重視のママ ハナコ
            "adventurous": "ai.png",       # 冒険家ケン (using ai.png as fallback)
            "romantic": "miyuki.png",      # ロマンチックなミユキ
            "local": "jiro.png",           # 地元愛のジロウ
            "officer": "gicho.png",        # 議長
            "system": "ai.png"             # システムメッセージ用
        }
    
    @lru_cache(maxsize=50)
    def get_avatar_path(self, persona_id: str) -> Optional[str]:
        """Get the path to a persona's avatar image"""
        icon_filename = self.persona_icon_map.get(persona_id, "ai.png")  # Default fallback
        original_path = self.icon_dir / icon_filename
        resized_path = self.resized_dir / icon_filename
        
        # Check if original exists
        if not original_path.exists():
            logger.warning(f"Avatar not found for {persona_id}: {original_path}")
            # Try fallback to ai.png
            fallback_path = self.icon_dir / "ai.png"
            if fallback_path.exists():
                return self._get_resized_avatar(fallback_path, self.resized_dir / "ai.png")
            return None
        
        return self._get_resized_avatar(original_path, resized_path)
    
    def _get_resized_avatar(self, original_path: Path, resized_path: Path) -> Optional[str]:
        """Resize avatar image if needed and return path to resized version"""
        try:
            # Check if resized version exists and is newer than original
            if (resized_path.exists() and 
                resized_path.stat().st_mtime >= original_path.stat().st_mtime):
                return str(resized_path)
            
            # Resize the image
            with Image.open(original_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize with high quality resampling
                resized_img = img.resize(self.avatar_size, Image.Resampling.LANCZOS)
                
                # Save as PNG to preserve transparency
                resized_img.save(resized_path, 'PNG', optimize=True)
                
                logger.info(f"Resized avatar: {original_path} -> {resized_path}")
                return str(resized_path)
                
        except Exception as e:
            logger.error(f"Error processing avatar {original_path}: {str(e)}")
            return None
    
    async def initialize_avatars(self):
        """Pre-process all available avatars"""
        try:
            tasks = []
            for persona_id in self.persona_icon_map.keys():
                # Run avatar processing in thread pool to avoid blocking
                task = asyncio.get_event_loop().run_in_executor(
                    None, self.get_avatar_path, persona_id
                )
                tasks.append(task)
            
            # Wait for all avatar processing to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if isinstance(r, str))
            logger.info(f"Initialized {successful}/{len(tasks)} avatars")
            
        except Exception as e:
            logger.error(f"Error initializing avatars: {str(e)}")
    
    def get_avatar_url(self, persona_id: str) -> str:
        """Get the URL for a persona's avatar"""
        # This will be the API endpoint URL
        return f"/api/avatar/{persona_id}"
    
    def list_available_avatars(self) -> Dict[str, str]:
        """List all available avatars with their URLs"""
        return {
            persona_id: self.get_avatar_url(persona_id)
            for persona_id in self.persona_icon_map.keys()
        }

# Global instance
avatar_service = AvatarService()