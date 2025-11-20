"""
Gestionnaire de téléchargement et traitement des médias WhatsApp
"""
import httpx
import os
from typing import Optional, Tuple
from app.config import Config
from app.utils import setup_logger, sanitize_filename, estimate_file_size_mb

logger = setup_logger(__name__)


class MediaHandler:
    """Gère le téléchargement et le traitement des médias WhatsApp"""
    
    def __init__(self):
        self.token = Config.WHATSAPP_TOKEN
        self.temp_dir = Config.TEMP_MEDIA_DIR
        Config.create_temp_dir()
    
    async def download_media(self, media_id: str) -> Optional[Tuple[str, str]]:
        """
        Télécharge un média depuis l'API Meta
        
        Args:
            media_id: ID du média fourni par WhatsApp
            
        Returns:
            Tuple (chemin_fichier, mime_type) ou None si échec
        """
        try:
            # Étape 1: Obtenir l'URL du média
            media_url = await self._get_media_url(media_id)
            if not media_url:
                logger.error(f"Impossible d'obtenir l'URL pour media_id: {media_id}")
                return None
            
            # Étape 2: Télécharger le fichier
            file_path, mime_type = await self._download_file(media_url, media_id)
            if not file_path:
                logger.error(f"Échec du téléchargement depuis {media_url}")
                return None
            
            # Étape 3: Vérifier la taille
            size_mb = estimate_file_size_mb(file_path)
            if size_mb > Config.MAX_MEDIA_SIZE_MB:
                logger.warning(f"Fichier trop volumineux: {size_mb}MB")
                os.remove(file_path)
                return None
            
            logger.info(f"Média téléchargé: {file_path} ({size_mb}MB)")
            return file_path, mime_type
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du média: {e}")
            return None
    
    async def _get_media_url(self, media_id: str) -> Optional[str]:
        """
        Récupère l'URL de téléchargement du média
        
        Args:
            media_id: ID du média
            
        Returns:
            URL de téléchargement ou None
        """
        url = f"https://graph.facebook.com/{Config.API_VERSION}/{media_id}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("url")
                else:
                    logger.error(f"Erreur API Meta: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'URL: {e}")
            return None
    
    async def _download_file(
        self,
        url: str,
        media_id: str
    ) -> Optional[Tuple[str, str]]:
        """
        Télécharge le fichier depuis l'URL
        
        Args:
            url: URL de téléchargement
            media_id: ID du média (pour le nom de fichier)
            
        Returns:
            Tuple (chemin_fichier, mime_type) ou None
        """
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Échec téléchargement: {response.status_code}")
                    return None
                
                # Déterminer le type MIME
                mime_type = response.headers.get("content-type", "application/octet-stream")
                
                # Déterminer l'extension
                extension = self._get_extension_from_mime(mime_type)
                
                # Créer le nom de fichier
                filename = sanitize_filename(f"{media_id}{extension}")
                file_path = os.path.join(self.temp_dir, filename)
                
                # Écrire le fichier
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                return file_path, mime_type
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du fichier: {e}")
            return None
    
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """
        Détermine l'extension de fichier à partir du MIME type
        
        Args:
            mime_type: Type MIME
            
        Returns:
            Extension avec le point (ex: ".jpg")
        """
        mime_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/mpeg": ".mpeg",
            "video/quicktime": ".mov",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/aac": ".aac",
            "application/pdf": ".pdf",
        }
        return mime_map.get(mime_type.lower(), ".bin")
    
    def cleanup_media(self, file_path: str) -> None:
        """
        Supprime un fichier média après traitement
        
        Args:
            file_path: Chemin du fichier à supprimer
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Fichier nettoyé: {file_path}")
        except Exception as e:
            logger.warning(f"Impossible de supprimer {file_path}: {e}")
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> None:
        """
        Supprime les fichiers temporaires anciens
        
        Args:
            max_age_hours: Age maximum en heures
        """
        try:
            import time
            now = time.time()
            cutoff = now - (max_age_hours * 3600)
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff:
                        os.remove(file_path)
                        logger.info(f"Ancien fichier supprimé: {filename}")
                        
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage: {e}")