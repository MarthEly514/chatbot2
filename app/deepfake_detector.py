"""
Détecteur de deepfakes pour images, vidéos et audios
"""
from transformers import pipeline
from PIL import Image
import cv2
import numpy as np
from typing import Dict, Optional
import asyncio
import os

from app.config import Config
from app.utils import setup_logger, get_media_type_from_mime

logger = setup_logger(__name__)


class DeepfakeDetector:
    """Détecteur de deepfakes multi-modal"""
    
    def __init__(self):
        self.image_model_name = Config.DEEPFAKE_IMAGE_MODEL
        self.threshold = Config.DEEPFAKE_THRESHOLD
        self.image_pipeline = None
        self._initialized = False
        logger.info("Initialisation du détecteur de deepfakes")
    
    def _lazy_load_image_model(self):
        """Charge le modèle de détection d'images (lazy loading)"""
        if self._initialized:
            return
        
        try:
            logger.info(f"Chargement du modèle deepfake image: {self.image_model_name}")
            
            # Charger le pipeline de classification d'images
            self.image_pipeline = pipeline(
                "image-classification",
                model=self.image_model_name,
                device=-1  # CPU
            )
            
            self._initialized = True
            logger.info("✅ Modèle deepfake image chargé")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            # Continuer sans modèle (analyse basique)
            self._initialized = True
    
    async def analyze_media(
        self,
        file_path: str,
        mime_type: str
    ) -> Dict[str, any]:
        """
        Analyse un média (image, vidéo ou audio)
        
        Args:
            file_path: Chemin du fichier média
            mime_type: Type MIME du fichier
            
        Returns:
            Dict avec les résultats de l'analyse
        """
        media_type = get_media_type_from_mime(mime_type)
        
        try:
            if media_type == "image":
                return await self.analyze_image(file_path)
            elif media_type == "video":
                return await self.analyze_video(file_path)
            elif media_type == "audio":
                return await self.analyze_audio(file_path)
            else:
                return {
                    "is_fake": False,
                    "confidence": 0.0,
                    "media_type": media_type,
                    "details": f"Type de média non supporté: {media_type}"
                }
                
        except Exception as e:
            logger.error(f"Erreur analyse média: {e}")
            return {
                "is_fake": False,
                "confidence": 0.0,
                "media_type": media_type,
                "details": f"Erreur d'analyse: {str(e)}"
            }
    
    async def analyze_image(self, image_path: str) -> Dict[str, any]:
        """
        Analyse une image pour détecter les deepfakes
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Dict avec les résultats
        """
        try:
            # Lazy loading du modèle
            if not self._initialized:
                self._lazy_load_image_model()
            
            # Vérifier que le fichier existe
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image non trouvée: {image_path}")
            
            # Charger l'image
            image = Image.open(image_path).convert("RGB")
            
            # Analyse avec le modèle si disponible
            if self.image_pipeline:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._analyze_image_with_model,
                    image
                )
            else:
                # Analyse basique sans modèle
                result = await self._analyze_image_basic(image_path)
            
            result["media_type"] = "image"
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse image: {e}")
            return {
                "is_fake": False,
                "confidence": 0.0,
                "media_type": "image",
                "details": f"Erreur: {str(e)}"
            }
    
    def _analyze_image_with_model(self, image: Image.Image) -> Dict[str, any]:
        """
        Analyse une image avec le modèle ML
        
        Args:
            image: Image PIL
            
        Returns:
            Dict avec les résultats
        """
        try:
            # Prédiction
            predictions = self.image_pipeline(image, top_k=2)
            
            # Parser les résultats
            top = predictions[0]
            label = top["label"].upper()
            score = top["score"]
            
            # Déterminer si c'est un deepfake
            is_fake = label in ["FAKE", "DEEPFAKE", "LABEL_1", "1", "MANIPULATED"]
            
            details = []
            details.append(f"• Prédiction: {label} ({int(score*100)}%)")
            
            if len(predictions) > 1:
                alt = predictions[1]
                details.append(f"• Alternative: {alt['label']} ({int(alt['score']*100)}%)")
            
            if is_fake:
                details.append("• Signes potentiels de manipulation détectés")
                details.append("• Vérifiez la source originale de l'image")
            else:
                details.append("• L'image semble authentique")
                details.append("• Aucun signe évident de manipulation IA")
            
            return {
                "is_fake": is_fake,
                "confidence": score,
                "label": label,
                "details": "\n".join(details),
                "all_predictions": predictions
            }
            
        except Exception as e:
            logger.error(f"Erreur dans _analyze_image_with_model: {e}")
            raise
    
    async def _analyze_image_basic(self, image_path: str) -> Dict[str, any]:
        """
        Analyse basique d'image sans modèle ML (analyse des artefacts)
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Dict avec les résultats
        """
        try:
            # Charger l'image avec OpenCV
            img = cv2.imread(image_path)
            
            if img is None:
                raise ValueError("Impossible de charger l'image")
            
            # Analyses basiques
            details = []
            suspicious_score = 0
            
            # 1. Vérifier la résolution
            height, width = img.shape[:2]
            details.append(f"• Résolution: {width}x{height}")
            
            # 2. Analyser les artefacts JPEG
            jpeg_quality = self._estimate_jpeg_quality(img)
            details.append(f"• Qualité estimée: {jpeg_quality}%")
            
            if jpeg_quality < 70:
                suspicious_score += 0.2
                details.append("• ⚠️ Qualité faible (possibles compressions multiples)")
            
            # 3. Analyser les bords (artefacts GAN typiques)
            edge_score = self._analyze_edges(img)
            if edge_score > 0.7:
                suspicious_score += 0.3
                details.append("• ⚠️ Artefacts de bords détectés")
            
            # Verdict
            is_fake = suspicious_score > 0.3
            confidence = min(suspicious_score, 0.6)  # Max 60% sans modèle ML
            
            if not is_fake:
                details.append("• Aucun artefact évident détecté")
            
            details.append("\n⚠️ Analyse limitée sans modèle ML")
            
            return {
                "is_fake": is_fake,
                "confidence": confidence,
                "label": "suspicious" if is_fake else "likely_real",
                "details": "\n".join(details)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse basique: {e}")
            raise
    
    def _estimate_jpeg_quality(self, img: np.ndarray) -> int:
        """Estime la qualité JPEG (méthode approximative)"""
        try:
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculer le bruit
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Estimer la qualité (approximation)
            quality = min(100, max(0, int(laplacian_var / 10)))
            return quality
        except:
            return 75  # Valeur par défaut
    
    def _analyze_edges(self, img: np.ndarray) -> float:
        """Analyse les artefacts de bords (typiques des GAN)"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Calculer le ratio de pixels de bord
            edge_ratio = np.sum(edges > 0) / edges.size
            
            return edge_ratio
        except:
            return 0.0
    
    async def analyze_video(self, video_path: str) -> Dict[str, any]:
        """
        Analyse une vidéo (sampling de frames)
        
        Args:
            video_path: Chemin de la vidéo
            
        Returns:
            Dict avec les résultats
        """
        try:
            logger.info(f"Analyse vidéo: {video_path}")
            
            # Ouvrir la vidéo
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError("Impossible d'ouvrir la vidéo")
            
            # Extraire quelques frames
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Analyser 5 frames échantillonnées
            frame_indices = np.linspace(0, total_frames - 1, min(5, total_frames), dtype=int)
            
            fake_count = 0
            confidences = []
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # Sauvegarder temporairement la frame
                    temp_frame = f"/tmp/frame_{idx}.jpg"
                    cv2.imwrite(temp_frame, frame)
                    
                    # Analyser la frame
                    result = await self.analyze_image(temp_frame)
                    
                    if result["is_fake"]:
                        fake_count += 1
                    confidences.append(result["confidence"])
                    
                    # Nettoyer
                    os.remove(temp_frame)
            
            cap.release()
            
            # Verdict global
            is_fake = fake_count >= 2  # Au moins 2 frames suspectes
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            details = [
                f"• Durée: {duration:.1f}s ({total_frames} frames)",
                f"• Frames analysées: {len(frame_indices)}",
                f"• Frames suspectes: {fake_count}/{len(frame_indices)}",
                f"• Confiance moyenne: {int(avg_confidence*100)}%"
            ]
            
            if is_fake:
                details.append("• ⚠️ Manipulations détectées dans certaines frames")
            else:
                details.append("• Vidéo semble authentique")
            
            return {
                "is_fake": is_fake,
                "confidence": avg_confidence,
                "media_type": "video",
                "details": "\n".join(details)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse vidéo: {e}")
            return {
                "is_fake": False,
                "confidence": 0.0,
                "media_type": "video",
                "details": f"Erreur: {str(e)}"
            }
    
    async def analyze_audio(self, audio_path: str) -> Dict[str, any]:
        """
        Analyse un audio (détection voix synthétique)
        
        Args:
            audio_path: Chemin de l'audio
            
        Returns:
            Dict avec les résultats
        """
        try:
            import librosa
            import soundfile as sf
            
            logger.info(f"Analyse audio: {audio_path}")
            
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Analyses basiques
            details = [
                f"• Durée: {duration:.1f}s",
                f"• Fréquence d'échantillonnage: {sr}Hz"
            ]
            
            # Analyse spectrale basique
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            mean_centroid = np.mean(spectral_centroid)
            
            details.append(f"• Centroïde spectral: {int(mean_centroid)}Hz")
            
            # Verdict (très basique sans modèle spécialisé)
            # Les audios synthétiques ont souvent des caractéristiques spectrales différentes
            is_suspicious = False
            confidence = 0.3  # Faible confiance sans modèle dédié
            
            details.append("\n⚠️ Analyse audio limitée")
            details.append("• Pour une analyse approfondie, consultez un expert")
            
            return {
                "is_fake": is_suspicious,
                "confidence": confidence,
                "media_type": "audio",
                "details": "\n".join(details)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse audio: {e}")
            return {
                "is_fake": False,
                "confidence": 0.0,
                "media_type": "audio",
                "details": f"Analyse audio non disponible: {str(e)}"
            }