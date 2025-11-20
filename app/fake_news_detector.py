"""
Détecteur de fake news utilisant des modèles NLP de Hugging Face
"""
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, Dict
from app.config import Config
from app.utils import setup_logger
import asyncio

logger = setup_logger(__name__)


class FakeNewsDetector:
    """Détecteur de fake news basé sur des modèles NLP"""
    
    def __init__(self):
        self.model_name = Config.FAKE_NEWS_MODEL
        self.threshold = Config.FAKE_NEWS_THRESHOLD
        self.pipeline = None
        self._initialized = False
        logger.info(f"Initialisation du détecteur de fake news: {self.model_name}")
    
    def _lazy_load_model(self):
        """Charge le modèle à la première utilisation (lazy loading)"""
        if self._initialized:
            return
        
        try:
            logger.info("Chargement du modèle de fake news...")
            
            # Charger le modèle et le tokenizer
            self.pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                device=-1,  # CPU (0 pour GPU si disponible)
                truncation=True,
                max_length=512
            )
            
            self._initialized = True
            logger.info("✅ Modèle de fake news chargé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement du modèle: {e}")
            raise
    
    async def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analyse un texte pour détecter les fake news
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dict avec les résultats de l'analyse
        """
        try:
            # Lazy loading du modèle
            if not self._initialized:
                self._lazy_load_model()
            
            # Valider le texte
            if not text or len(text.strip()) < 10:
                return {
                    "is_fake": False,
                    "confidence": 0.0,
                    "label": "insufficient_text",
                    "details": "Texte trop court pour une analyse fiable"
                }
            
            # Limiter la longueur
            text = text[:5000]
            
            # Analyser avec le modèle
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._analyze_with_model, text)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du texte: {e}")
            return {
                "is_fake": False,
                "confidence": 0.0,
                "label": "error",
                "details": f"Erreur d'analyse: {str(e)}"
            }
    
    def _analyze_with_model(self, text: str) -> Dict[str, any]:
        """
        Effectue l'analyse avec le modèle (méthode synchrone)
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dict avec les résultats
        """
        try:
            # Prédiction
            predictions = self.pipeline(text, top_k=2)
            
            # Parser les résultats selon le format du modèle
            result = self._parse_predictions(predictions)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur dans _analyze_with_model: {e}")
            raise
    
    def _parse_predictions(self, predictions: list) -> Dict[str, any]:
        """
        Parse les prédictions du modèle
        
        Args:
            predictions: Résultats bruts du modèle
            
        Returns:
            Dict formaté avec les résultats
        """
        # Format typique: [{"label": "FAKE"/"REAL", "score": 0.95}, ...]
        if not predictions or len(predictions) == 0:
            return {
                "is_fake": False,
                "confidence": 0.0,
                "label": "unknown",
                "details": "Aucune prédiction disponible"
            }
        
        # Prendre la prédiction avec le meilleur score
        top_prediction = predictions[0]
        label = top_prediction["label"].upper()
        score = top_prediction["score"]
        
        # Déterminer si c'est fake
        # Le label peut être "FAKE", "REAL", "fake", "real", "0", "1", etc.
        is_fake = label in ["FAKE", "LABEL_1", "1", "UNRELIABLE"]
        
        # Si le modèle prédit "REAL" avec haute confiance, c'est pas fake
        if label in ["REAL", "LABEL_0", "0", "RELIABLE"]:
            is_fake = False
            # Inverser le score pour représenter la confiance que c'est réel
            confidence = score
        else:
            confidence = score
        
        # Détails supplémentaires
        details = self._generate_details(label, confidence, predictions)
        
        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "label": label,
            "details": details,
            "all_predictions": predictions
        }
    
    def _generate_details(
        self,
        label: str,
        confidence: float,
        predictions: list
    ) -> str:
        """
        Génère des détails explicatifs pour l'utilisateur
        
        Args:
            label: Label prédit
            confidence: Score de confiance
            predictions: Toutes les prédictions
            
        Returns:
            String avec les détails
        """
        details = []
        
        # Interprétation du score
        if confidence >= 0.9:
            details.append("• Confiance très élevée dans l'analyse")
        elif confidence >= 0.7:
            details.append("• Confiance élevée dans l'analyse")
        elif confidence >= 0.5:
            details.append("• Confiance modérée dans l'analyse")
        else:
            details.append("• Confiance faible - résultats à prendre avec précaution")
        
        # Conseils selon le label
        if label in ["FAKE", "LABEL_1", "1"]:
            details.append("• Vérifiez les sources citées")
            details.append("• Recherchez des confirmations sur des sites fiables")
            details.append("• Méfiez-vous des titres sensationnalistes")
        else:
            details.append("• Le contenu semble authentique mais restez vigilant")
            details.append("• Vérifiez toujours le contexte et la date")
        
        # Afficher les scores alternatifs si disponibles
        if len(predictions) > 1:
            alt = predictions[1]
            details.append(f"• Score alternatif: {alt['label']} ({int(alt['score']*100)}%)")
        
        return "\n".join(details)
    
    def get_analysis_summary(self, analysis: Dict[str, any]) -> str:
        """
        Génère un résumé textuel de l'analyse
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résumé formaté
        """
        is_fake = analysis["is_fake"]
        confidence = analysis["confidence"]
        details = analysis.get("details", "")
        
        if is_fake:
            summary = f"🚨 **ALERTE FAKE NEWS POSSIBLE**\n\n"
            summary += f"📊 Probabilité : {int(confidence * 100)}%\n\n"
            summary += "Ce texte présente des caractéristiques typiques de désinformation.\n\n"
        else:
            summary += f"✅ **CONTENU PROBABLEMENT FIABLE**\n\n"
            summary += f"📊 Probabilité : {int(confidence * 100)}%\n\n"
            summary += "Ce texte ne présente pas de signes évidents de désinformation.\n\n"
        
        if details:
            summary += f"**Détails :**\n{details}\n\n"
        
        summary += (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ **Rappel Important :**\n"
            "Cette analyse automatique n'est pas infaillible.\n"
            "Vérifiez toujours :\n"
            "• Les sources primaires\n"
            "• Les sites de fact-checking\n"
            "• Le contexte de publication\n"
            "• La date et l'auteur"
        )
        
        return summary