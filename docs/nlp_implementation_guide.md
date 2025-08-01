# Nova Agent NLP Implementation Guide

## Overview

This guide provides a detailed implementation plan for replacing the basic string matching in `nova/phases/analyze_phase.py` with a sophisticated NLP intent classification system.

## 🎯 **Implementation Goals**

1. **Replace basic string matching** with advanced NLP intent detection
2. **Improve accuracy** through multiple classification methods
3. **Add context awareness** for better understanding
4. **Enable continuous learning** through training data collection
5. **Maintain backward compatibility** during transition

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Intent Classifier│───▶│  Action Planning │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Context Manager  │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Training Data    │
                       │ Manager          │
                       └──────────────────┘
```

## 📋 **Implementation Steps**

### **Phase 1: Core NLP Infrastructure** ✅

#### 1.1 Create Intent Classification System
- **File**: `nova/nlp/intent_classifier.py`
- **Purpose**: Multi-method intent classification
- **Methods**:
  - Rule-based (regex patterns)
  - Semantic similarity (embeddings)
  - AI-powered (OpenAI classification)

#### 1.2 Create Context Management System
- **File**: `nova/nlp/context_manager.py`
- **Purpose**: Track conversation history and system state
- **Features**:
  - Conversation history
  - System state tracking
  - User preferences
  - Time-based context

#### 1.3 Create Training Data Management
- **File**: `nova/nlp/training_data.py`
- **Purpose**: Collect and manage training data
- **Features**:
  - Training example collection
  - User feedback handling
  - Data quality reporting
  - Export capabilities

### **Phase 2: Integration with Existing System**

#### 2.1 Update Analyze Phase
- **File**: `nova/phases/analyze_phase.py`
- **Changes**:
  - Replace simple string matching
  - Integrate advanced NLP classification
  - Add context awareness
  - Maintain backward compatibility

#### 2.2 Update Plan Phase
- **File**: `nova/phases/plan_phase.py`
- **Changes**:
  - Handle new analysis structure
  - Add confidence-based planning
  - Include entity extraction
  - Add execution strategies

#### 2.3 Update Execute Phase
- **File**: `nova/phases/execute_phase.py`
- **Changes**:
  - Handle new action types
  - Add parameter validation
  - Implement execution strategies
  - Add error handling

### **Phase 3: Testing and Validation**

#### 3.1 Create Comprehensive Tests
- **File**: `tests/test_nlp_intent_classification.py`
- **Coverage**:
  - Intent classification accuracy
  - Context management
  - Training data handling
  - Edge cases and errors

#### 3.2 Performance Testing
- **Metrics**:
  - Classification accuracy
  - Response time
  - Memory usage
  - Error rates

### **Phase 4: Training and Optimization**

#### 4.1 Initial Training Data
- **Sources**:
  - Existing conversation logs
  - Manual annotation
  - Synthetic examples
  - User feedback

#### 4.2 Continuous Learning
- **Process**:
  - Collect real user interactions
  - Gather feedback on misclassifications
  - Update patterns and examples
  - Retrain models periodically

## 🔧 **Technical Implementation Details**

### **Intent Types Supported**

```python
class IntentType(Enum):
    # System Control
    RESUME_LOOP = "resume_loop"
    PAUSE_LOOP = "pause_loop"
    STOP_LOOP = "stop_loop"
    STATUS_CHECK = "status_check"
    
    # Analytics & Reporting
    GET_RPM = "get_rpm"
    GET_ANALYTICS = "get_analytics"
    GET_PERFORMANCE = "get_performance"
    GET_REPORTS = "get_reports"
    
    # Content Management
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    SCHEDULE_CONTENT = "schedule_content"
    
    # Avatar Management
    SWITCH_AVATAR = "switch_avatar"
    CONFIGURE_AVATAR = "configure_avatar"
    AVATAR_PERFORMANCE = "avatar_performance"
    
    # Platform Management
    PLATFORM_STATUS = "platform_status"
    CONNECT_PLATFORM = "connect_platform"
    DISCONNECT_PLATFORM = "disconnect_platform"
    
    # Memory & Learning
    QUERY_MEMORY = "query_memory"
    LEARN_FROM_DATA = "learn_from_data"
    OPTIMIZE_PROMPTS = "optimize_prompts"
    
    # Configuration
    UPDATE_CONFIG = "update_config"
    GET_CONFIG = "get_config"
    RESET_CONFIG = "reset_config"
    
    # Emergency & Debug
    EMERGENCY_STOP = "emergency_stop"
    DEBUG_MODE = "debug_mode"
    SYSTEM_HEALTH = "system_health"
    
    # Generic
    CHAT = "chat"
    HELP = "help"
    UNKNOWN = "unknown"
```

### **Classification Methods**

#### 1. Rule-Based Classification
```python
# Regex patterns for each intent
intent_patterns = {
    IntentType.RESUME_LOOP: [
        r'\b(resume|start|begin|continue|restart)\b',
        r'\b(turn on|activate|enable)\b.*\b(loop|system|nova)\b',
        r'\b(get|make)\b.*\b(going|running)\b'
    ],
    IntentType.GET_RPM: [
        r'\b(rpm|revenue|earnings|money|income)\b',
        r'\b(how much|what is|show me)\b.*\b(making|earning)\b',
        r'\b(performance|metrics|stats)\b.*\b(revenue|money)\b'
    ]
}
```

#### 2. Semantic Classification
```python
# Uses sentence transformers for similarity matching
embedder = SentenceTransformer('all-MiniLM-L6-v2')
message_embedding = embedder.encode([message])[0]
# Compare with example embeddings for each intent
```

#### 3. AI-Powered Classification
```python
# Uses OpenAI for complex intent classification
prompt = f"""Classify the user's intent from the following message.
Choose from these intent types: {intent_types}

Message: "{message}"

Respond with JSON only:
{{
    "intent": "intent_type_value",
    "confidence": 0.0-1.0,
    "entities": {{"key": "value"}},
    "reasoning": "brief explanation"
}}"""
```

### **Context Management**

```python
@dataclass
class SystemState:
    loop_active: bool
    current_avatar: str
    last_rpm_check: float
    last_content_created: float
    active_platforms: List[str]
    current_task: Optional[str]
    error_count: int
    performance_metrics: Dict[str, float]

@dataclass
class ConversationTurn:
    timestamp: float
    user_message: str
    system_response: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    context_snapshot: Dict[str, Any]
```

### **Training Data Structure**

```python
@dataclass
class TrainingExample:
    message: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: float
    user_feedback: Optional[str] = None
    corrected_intent: Optional[str] = None
    source: str = "user_input"
```

## 🚀 **Usage Examples**

### **Basic Intent Classification**
```python
from nova.nlp import classify_intent, get_context_for_intent

# Get context for better classification
context = get_context_for_intent("resume the system")

# Classify intent
result = classify_intent("resume the system", context)

print(f"Intent: {result.intent.value}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Method: {result.classification_method}")
print(f"Entities: {result.entities}")
```

### **Context-Aware Classification**
```python
from nova.nlp import update_system_state

# Update system state
update_system_state(loop_active=True, current_avatar="Avatar 1")

# Classify with context
context = get_context_for_intent("what's the status")
result = classify_intent("what's the status", context)

# Context will help determine this is a status check
```

### **Training Data Collection**
```python
from nova.nlp.training_data import add_training_example, add_user_feedback

# Add training example
add_training_example(
    message="resume the system",
    intent="resume_loop",
    confidence=0.95,
    entities={},
    context={}
)

# Add user feedback for correction
add_user_feedback(
    original_intent="chat",
    corrected_intent="resume_loop",
    message="start nova",
    feedback="This should be resume_loop, not chat"
)
```

## 📊 **Performance Metrics**

### **Accuracy Targets**
- **Rule-based**: 85%+ for common intents
- **Semantic**: 75%+ for similar phrases
- **AI-powered**: 90%+ for complex cases
- **Overall**: 80%+ combined accuracy

### **Response Time Targets**
- **Rule-based**: < 10ms
- **Semantic**: < 100ms
- **AI-powered**: < 1000ms
- **Overall**: < 500ms average

### **Memory Usage**
- **Context history**: < 10MB
- **Training data**: < 100MB
- **Model embeddings**: < 500MB

## 🔄 **Continuous Improvement**

### **Data Collection Strategy**
1. **Automatic collection** of all user interactions
2. **Manual annotation** of edge cases
3. **User feedback** on misclassifications
4. **A/B testing** of new patterns

### **Retraining Schedule**
- **Weekly**: Update patterns based on feedback
- **Monthly**: Retrain semantic models
- **Quarterly**: Full system evaluation

### **Quality Monitoring**
- **Accuracy tracking** over time
- **Error analysis** for common failures
- **User satisfaction** metrics
- **Performance monitoring**

## 🛠️ **Installation and Setup**

### **Dependencies**
```bash
pip install sentence-transformers numpy scikit-learn
```

### **Configuration**
```python
# Add to config/settings.yaml
nlp:
  confidence_threshold: 0.7
  max_context_history: 50
  training_data_dir: "data/nlp_training"
  enable_ai_classification: true
  enable_semantic_classification: true
```

### **Environment Variables**
```bash
# Optional: Custom model paths
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
OPENAI_MODEL=gpt-4o-mini
```

## 🧪 **Testing Strategy**

### **Unit Tests**
- Intent classification accuracy
- Context management
- Training data handling
- Error scenarios

### **Integration Tests**
- End-to-end pipeline
- Performance under load
- Memory usage
- Error recovery

### **User Acceptance Tests**
- Real user scenarios
- Edge cases
- Performance expectations
- Usability feedback

## 📈 **Success Metrics**

### **Short-term (1-2 weeks)**
- [ ] Basic NLP system implemented
- [ ] All tests passing
- [ ] Backward compatibility maintained
- [ ] Performance targets met

### **Medium-term (1-2 months)**
- [ ] 80%+ classification accuracy
- [ ] Training data collection active
- [ ] User feedback system working
- [ ] Performance optimized

### **Long-term (3-6 months)**
- [ ] 90%+ classification accuracy
- [ ] Self-improving system
- [ ] Advanced context awareness
- [ ] Production deployment

## 🔧 **Troubleshooting**

### **Common Issues**

#### Low Classification Accuracy
- **Check**: Training data quality
- **Solution**: Add more examples, improve patterns

#### Slow Response Times
- **Check**: Model loading, caching
- **Solution**: Optimize embeddings, add caching

#### Memory Issues
- **Check**: Context history size
- **Solution**: Implement cleanup, reduce history

#### Integration Errors
- **Check**: Import paths, dependencies
- **Solution**: Verify installation, check logs

### **Debug Mode**
```python
import logging
logging.getLogger('nova.nlp').setLevel(logging.DEBUG)

# Enable detailed logging for troubleshooting
```

## 📚 **Additional Resources**

- **Sentence Transformers**: https://www.sbert.net/
- **OpenAI API**: https://platform.openai.com/docs
- **NLP Best Practices**: https://spacy.io/usage
- **Testing Guidelines**: https://pytest.org/

---

This implementation guide provides a comprehensive roadmap for replacing the basic string matching with a sophisticated NLP system. The modular design ensures easy maintenance and continuous improvement while maintaining backward compatibility. 