"""
Training Data Management for Nova Agent NLP

This module manages training data collection, validation, and improvement
for the intent classification system.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import random

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """Represents a training example for intent classification"""
    message: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: float
    user_feedback: Optional[str] = None
    corrected_intent: Optional[str] = None
    source: str = "user_input"

@dataclass
class IntentTrainingData:
    """Training data for a specific intent"""
    intent: str
    examples: List[TrainingExample]
    patterns: List[str]
    synonyms: List[str]
    common_entities: List[str]

class TrainingDataManager:
    """Manages training data for NLP improvement"""
    
    def __init__(self, data_dir: str = "data/nlp_training"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.examples_file = self.data_dir / "training_examples.json"
        self.intents_file = self.data_dir / "intent_data.json"
        self.feedback_file = self.data_dir / "user_feedback.json"
        
        # Load existing data
        self.training_examples = self._load_training_examples()
        self.intent_data = self._load_intent_data()
        self.user_feedback = self._load_user_feedback()
        
    def add_training_example(self, example: TrainingExample):
        """Add a new training example"""
        self.training_examples.append(example)
        self._save_training_examples()
        logger.info(f"Added training example for intent: {example.intent}")
        
    def add_user_feedback(self, original_intent: str, corrected_intent: str, 
                         message: str, feedback: str):
        """Add user feedback for intent correction"""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "original_intent": original_intent,
            "corrected_intent": corrected_intent,
            "message": message,
            "feedback": feedback
        }
        
        self.user_feedback.append(feedback_entry)
        self._save_user_feedback()
        logger.info(f"Added user feedback: {original_intent} -> {corrected_intent}")
        
    def get_training_examples(self, intent: Optional[str] = None) -> List[TrainingExample]:
        """Get training examples, optionally filtered by intent"""
        if intent:
            return [ex for ex in self.training_examples if ex.intent == intent]
        return self.training_examples.copy()
        
    def get_intent_data(self, intent: str) -> Optional[IntentTrainingData]:
        """Get training data for a specific intent"""
        return self.intent_data.get(intent)
        
    def update_intent_patterns(self, intent: str, patterns: List[str]):
        """Update regex patterns for an intent"""
        if intent not in self.intent_data:
            self.intent_data[intent] = IntentTrainingData(
                intent=intent,
                examples=[],
                patterns=patterns,
                synonyms=[],
                common_entities=[]
            )
        else:
            self.intent_data[intent].patterns = patterns
            
        self._save_intent_data()
        logger.info(f"Updated patterns for intent: {intent}")
        
    def add_intent_synonyms(self, intent: str, synonyms: List[str]):
        """Add synonyms for an intent"""
        if intent not in self.intent_data:
            self.intent_data[intent] = IntentTrainingData(
                intent=intent,
                examples=[],
                patterns=[],
                synonyms=synonyms,
                common_entities=[]
            )
        else:
            self.intent_data[intent].synonyms.extend(synonyms)
            
        self._save_intent_data()
        logger.info(f"Added synonyms for intent: {intent}")
        
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate a report on training data quality"""
        report = {
            "total_examples": len(self.training_examples),
            "intents_covered": len(set(ex.intent for ex in self.training_examples)),
            "examples_per_intent": {},
            "feedback_count": len(self.user_feedback),
            "data_quality_score": self._calculate_quality_score(),
            "recommendations": self._generate_recommendations()
        }
        
        # Count examples per intent
        for example in self.training_examples:
            intent = example.intent
            if intent not in report["examples_per_intent"]:
                report["examples_per_intent"][intent] = 0
            report["examples_per_intent"][intent] += 1
            
        return report
        
    def export_training_data(self, format: str = "json") -> str:
        """Export training data in specified format"""
        if format == "json":
            return json.dumps({
                "training_examples": [asdict(ex) for ex in self.training_examples],
                "intent_data": {k: asdict(v) for k, v in self.intent_data.items()},
                "user_feedback": self.user_feedback
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _load_training_examples(self) -> List[TrainingExample]:
        """Load training examples from file"""
        if self.examples_file.exists():
            try:
                with open(self.examples_file, 'r') as f:
                    data = json.load(f)
                return [TrainingExample(**ex) for ex in data]
            except Exception as e:
                logger.error(f"Failed to load training examples: {e}")
        return []
        
    def _load_intent_data(self) -> Dict[str, IntentTrainingData]:
        """Load intent training data from file"""
        if self.intents_file.exists():
            try:
                with open(self.intents_file, 'r') as f:
                    data = json.load(f)
                return {k: IntentTrainingData(**v) for k, v in data.items()}
            except Exception as e:
                logger.error(f"Failed to load intent data: {e}")
        return {}
        
    def _load_user_feedback(self) -> List[Dict[str, Any]]:
        """Load user feedback from file"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load user feedback: {e}")
        return []
        
    def _save_training_examples(self):
        """Save training examples to file"""
        try:
            with open(self.examples_file, 'w') as f:
                json.dump([asdict(ex) for ex in self.training_examples], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save training examples: {e}")
            
    def _save_intent_data(self):
        """Save intent data to file"""
        try:
            with open(self.intents_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.intent_data.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save intent data: {e}")
            
    def _save_user_feedback(self):
        """Save user feedback to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.user_feedback, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user feedback: {e}")
            
    def _calculate_quality_score(self) -> float:
        """Calculate overall data quality score"""
        if not self.training_examples:
            return 0.0
            
        # Factors to consider:
        # 1. Coverage of intents
        # 2. Number of examples per intent
        # 3. User feedback quality
        # 4. Pattern coverage
        
        intent_coverage = len(set(ex.intent for ex in self.training_examples)) / 20  # Assuming 20 total intents
        avg_examples = len(self.training_examples) / max(1, len(set(ex.intent for ex in self.training_examples)))
        feedback_quality = min(1.0, len(self.user_feedback) / 100)  # Normalize to 0-1
        
        score = (intent_coverage * 0.4 + 
                min(1.0, avg_examples / 10) * 0.4 + 
                feedback_quality * 0.2)
                
        return round(score, 2)
        
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving training data"""
        recommendations = []
        
        # Check intent coverage
        covered_intents = set(ex.intent for ex in self.training_examples)
        all_intents = set(self.intent_data.keys())
        missing_intents = all_intents - covered_intents
        
        if missing_intents:
            recommendations.append(f"Add training examples for missing intents: {', '.join(missing_intents)}")
            
        # Check examples per intent
        intent_counts = {}
        for example in self.training_examples:
            intent_counts[example.intent] = intent_counts.get(example.intent, 0) + 1
            
        for intent, count in intent_counts.items():
            if count < 5:
                recommendations.append(f"Add more examples for '{intent}' (currently {count})")
                
        # Check feedback
        if len(self.user_feedback) < 10:
            recommendations.append("Collect more user feedback to improve accuracy")
            
        return recommendations

# Global training data manager instance
training_data_manager = TrainingDataManager()

def add_training_example(message: str, intent: str, confidence: float, 
                        entities: Dict[str, Any], context: Dict[str, Any]):
    """Convenience function to add training example"""
    example = TrainingExample(
        message=message,
        intent=intent,
        confidence=confidence,
        entities=entities,
        context=context,
        timestamp=datetime.now().timestamp()
    )
    training_data_manager.add_training_example(example)

def add_user_feedback(original_intent: str, corrected_intent: str, 
                     message: str, feedback: str):
    """Convenience function to add user feedback"""
    training_data_manager.add_user_feedback(original_intent, corrected_intent, message, feedback) 