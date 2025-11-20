"""
Processeur principal des messages WhatsApp
Route les messages vers les détecteurs appropriés
"""
from typing import Dict, Optional
from app.config import Config
from app.sender import send_text_message
from app.media_handler import MediaHandler
from app.fake_news_detector import FakeNewsDetector
from app.deepfake_detector import DeepfakeDetector
from app.utils import setup_logger, format_analysis_result, get_media_type_from_mime

logger = setup_logger(__name__)


class MessageProcessor:
    """Processeur principal des messages entrants"""
    
    def __init__(self):
        self.media_handler = MediaHandler()
        self.fake_news_detector = FakeNewsDetector()
        self.deepfake_detector = DeepfakeDetector()
        logger.info("MessageProcessor initialisé")
    
    async def process_incoming_message(self, message_data: Dict) -> None:
        """
        Traite un message entrant
        
        Args:
            message_data: Données du message parsées depuis le webhook
        """
        try:
            from_number = message_data.get("from")
            message_type = message_data.get("type")
            
            logger.info(f"Message de {from_number}, type: {message_type}")
            
            # Router selon le type de message
            if message_type == "text":
                await self._handle_text_message(from_number, message_data)
            
            elif message_type in ["image", "video", "audio", "document"]:
                await self._handle_media_message(from_number, message_data, message_type)
            
            else:
                await send_text_message(
                    from_number,
                    f"❌ Type de message non supporté: {message_type}\n\n"
                    f"Envoyez-moi du texte ou des médias (image/vidéo/audio) à analyser."
                )
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}", exc_info=True)
            # Tenter d'informer l'utilisateur
            try:
                await send_text_message(
                    message_data.get("from"),
                    "❌ Désolé, une erreur s'est produite lors du traitement de votre message."
                )
            except:
                pass
    
    async def _handle_text_message(self, from_number: str, message_data: Dict) -> None:
        """
        Traite un message texte
        
        Args:
            from_number: Numéro de l'expéditeur
            message_data: Données du message
        """
        text_body = message_data.get("text", {}).get("body", "").strip()
        
        if not text_body:
            await send_text_message(from_number, "❌ Message vide reçu.")
            return
        
        # Commandes spéciales
        text_lower = text_body.lower()
        
        if text_lower in ["start", "hello", "bonjour", "salut", "hi"]:
            await send_text_message(from_number, Config.WELCOME_MESSAGE)
            return
        
        elif text_lower in ["help", "aide", "?"]:
            await send_text_message(from_number, Config.HELP_MESSAGE)
            return
        
        elif text_lower in ["info", "about", "à propos"]:
            await send_text_message(from_number, Config.INFO_MESSAGE)
            return
        
        # Analyser le texte pour les fake news
        await send_text_message(
            from_number,
            "🔍 Analyse en cours...\n\nCela peut prendre quelques secondes."
        )
        
        try:
            # Analyse fake news
            analysis = await self.fake_news_detector.analyze_text(text_body)
            
            # Formater et envoyer le résultat
            result_message = self.fake_news_detector.get_analysis_summary(analysis)
            await send_text_message(from_number, result_message)
            
            logger.info(f"Analyse texte terminée pour {from_number}: fake={analysis['is_fake']}")
            
        except Exception as e:
            logger.error(f"Erreur analyse texte: {e}")
            await send_text_message(
                from_number,
                "❌ Erreur lors de l'analyse du texte. Veuillez réessayer."
            )
    
    async def _handle_media_message(
        self,
        from_number: str,
        message_data: Dict,
        media_type: str
    ) -> None:
        """
        Traite un message contenant un média
        
        Args:
            from_number: Numéro de l'expéditeur
            message_data: Données du message
            media_type: Type de média (image, video, audio, document)
        """
        try:
            # Extraire les infos du média
            media_data = message_data.get(media_type, {})
            media_id = media_data.get("id")
            mime_type = media_data.get("mime_type", "application/octet-stream")
            
            if not media_id:
                await send_text_message(
                    from_number,
                    "❌ Impossible de récupérer le média."
                )
                return
            
            # Informer l'utilisateur
            await send_text_message(
                from_number,
                f"📥 Téléchargement du média en cours...\n\n"
                f"Type: {media_type}\n"
                f"Cela peut prendre jusqu'à 30 secondes."
            )
            
            # Télécharger le média
            result = await self.media_handler.download_media(media_id)
            
            if not result:
                await send_text_message(
                    from_number,
                    "❌ Échec du téléchargement du média.\n"
                    "Vérifiez que le fichier n'est pas trop volumineux (<16MB)."
                )
                return
            
            file_path, mime_type = result
            
            # Informer que l'analyse commence
            await send_text_message(
                from_number,
                "🔍 Analyse en cours...\n\n"
                "Détection de deepfakes et manipulations."
            )
            
            # Analyser le média
            analysis = await self.deepfake_detector.analyze_media(file_path, mime_type)
            
            # Formater le résultat
            content_type = get_media_type_from_mime(mime_type)
            result_message = format_analysis_result(
                content_type=content_type,
                is_fake=analysis["is_fake"],
                confidence=analysis["confidence"],
                details=analysis.get("details", "")
            )
            
            # Envoyer le résultat
            await send_text_message(from_number, result_message)
            
            logger.info(
                f"Analyse média terminée pour {from_number}: "
                f"type={content_type}, fake={analysis['is_fake']}"
            )
            
            # Nettoyer le fichier temporaire
            self.media_handler.cleanup_media(file_path)
            
        except Exception as e:
            logger.error(f"Erreur traitement média: {e}", exc_info=True)
            await send_text_message(
                from_number,
                "❌ Erreur lors de l'analyse du média.\n"
                "Veuillez réessayer avec un fichier différent."
            )
    
    async def send_welcome_to_new_user(self, phone_number: str) -> None:
        """
        Envoie le message de bienvenue à un nouvel utilisateur
        
        Args:
            phone_number: Numéro de téléphone de l'utilisateur
        """
        try:
            await send_text_message(phone_number, Config.WELCOME_MESSAGE)
            logger.info(f"Message de bienvenue envoyé à {phone_number}")
        except Exception as e:
            logger.error(f"Erreur envoi bienvenue: {e}")