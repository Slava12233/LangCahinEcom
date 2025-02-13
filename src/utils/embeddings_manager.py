"""
מודול לניהול embeddings באמצעות sentence-transformers.
מאפשר חיפוש סמנטי בשאלות נפוצות.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils import get_logger
from .constants import QuestionCategory, QuestionIntent, CATEGORY_KEYWORDS
from .faq import FAQEntry, INITIAL_FAQS

logger = get_logger(__name__)

class EmbeddingsManager:
    def __init__(self, threshold: float = 0.7):
        """
        אתחול מנהל ה-embeddings
        
        Args:
            threshold: סף דמיון מינימלי לחיפוש שאלות דומות
        """
        self.threshold = threshold
        self.model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
        self.faq_entries: List[FAQEntry] = []
        self._initialize_faq()
        
        logger.info(
            "מנהל ה-embeddings אותחל",
            extra={
                "model": self.model.get_sentence_embedding_dimension(),
                "threshold": threshold,
                "faq_count": len(self.faq_entries)
            }
        )

    def _initialize_faq(self) -> None:
        """אתחול מאגר השאלות הנפוצות"""
        try:
            # חישוב embeddings לכל השאלות
            for entry in INITIAL_FAQS:
                entry.embedding = self._calculate_embedding(entry.question)
                self.faq_entries.append(entry)
                
            logger.info(
                "מאגר השאלות הנפוצות אותחל",
                extra={"entries_count": len(self.faq_entries)}
            )
            
        except Exception as e:
            logger.error(
                "שגיאה באתחול מאגר השאלות",
                extra={"error": str(e)}
            )

    def _calculate_embedding(self, text: str) -> List[float]:
        """חישוב embedding לטקסט"""
        return self.model.encode(text).tolist()

    def _identify_category(self, query: str) -> str:
        """זיהוי קטגוריה לפי מילות מפתח"""
        query_lower = query.lower()
        max_matches = 0
        best_category = QuestionCategory.GENERAL

        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > max_matches:
                max_matches = matches
                best_category = category

        logger.debug(
            "זוהתה קטגוריה",
            extra={
                "query": query,
                "category": best_category,
                "matches": max_matches
            }
        )

        return best_category

    def find_similar_questions(
        self, 
        query: str, 
        threshold: Optional[float] = None,
        top_k: int = 3
    ) -> List[Tuple[str, str, float, str]]:  # הוספנו את הכוונה לתוצאה
        """
        חיפוש שאלות דומות
        
        Args:
            query: שאלת המשתמש
            threshold: סף דמיון מינימלי (אופציונלי)
            top_k: כמה תוצאות להחזיר
            
        Returns:
            רשימה של טאפלים (שאלה, תשובה, ציון דמיון, כוונה)
        """
        if threshold is None:
            threshold = self.threshold

        try:
            # זיהוי קטגוריה
            category = self._identify_category(query)
            
            # חישוב embedding לשאלה
            query_embedding = self._calculate_embedding(query)
            
            # חישוב דמיון לכל השאלות
            similarities = []
            for entry in self.faq_entries:
                if entry.embedding:
                    similarity = self._calculate_similarity(query_embedding, entry.embedding)
                    # תעדוף שאלות מאותה קטגוריה
                    if entry.category == category:
                        similarity *= 1.2
                    # בדיקה אם השאלה מופיעה בדוגמאות
                    if query.lower() in [ex.lower() for ex in entry.examples]:
                        similarity *= 1.3
                    similarities.append((entry, similarity))

            # מיון לפי ציון דמיון
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # סינון לפי סף והחזרת התוצאות הטובות ביותר
            results = [
                (entry.question, entry.answer, score, entry.intent)
                for entry, score in similarities[:top_k]
                if score >= threshold
            ]

            logger.info(
                "נמצאו התאמות לשאלה",
                extra={
                    "query": query,
                    "matches_count": len(results),
                    "threshold": threshold,
                    "top_score": results[0][2] if results else 0,
                    "category": category
                }
            )

            return results

        except Exception as e:
            logger.error(
                "שגיאה בחיפוש שאלות דומות",
                extra={
                    "error": str(e),
                    "query": query
                }
            )
            return []

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """חישוב דמיון קוסינוס בין שני וקטורים"""
        try:
            return float(cosine_similarity(
                np.array(vec1).reshape(1, -1),
                np.array(vec2).reshape(1, -1)
            )[0][0])
        except Exception as e:
            logger.error(
                "שגיאה בחישוב דמיון",
                extra={"error": str(e)}
            )
            return 0.0

    def add_faq(self, entry: FAQEntry) -> bool:
        """
        הוספת שאלה נפוצה חדשה
        
        Args:
            entry: אובייקט FAQEntry
            
        Returns:
            האם ההוספה הצליחה
        """
        try:
            entry.embedding = self._calculate_embedding(entry.question)
            self.faq_entries.append(entry)
            
            logger.info(
                "נוספה שאלה נפוצה חדשה",
                extra={
                    "question": entry.question,
                    "category": entry.category,
                    "intent": entry.intent
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                "שגיאה בהוספת שאלה נפוצה",
                extra={
                    "error": str(e),
                    "question": entry.question
                }
            )
            return False

    def get_faq_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות על מאגר השאלות הנפוצות"""
        try:
            categories = self._analyze_categories()
            
            stats = {
                "total_entries": len(self.faq_entries),
                "categories": categories,
                "intents": self._analyze_intents(),
                "avg_examples_per_entry": sum(
                    len(entry.examples) for entry in self.faq_entries
                ) / len(self.faq_entries) if self.faq_entries else 0
            }
            
            logger.info(
                "סטטיסטיקות FAQ",
                extra=stats
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "שגיאה בקבלת סטטיסטיקות",
                extra={"error": str(e)}
            )
            return {
                "error": str(e)
            }

    def _analyze_categories(self) -> Dict[str, int]:
        """ניתוח התפלגות קטגוריות"""
        categories = {}
        for entry in self.faq_entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        return categories

    def _analyze_intents(self) -> Dict[str, int]:
        """ניתוח התפלגות כוונות"""
        intents = {}
        for entry in self.faq_entries:
            intents[entry.intent] = intents.get(entry.intent, 0) + 1
        return intents