"""
News Analysis Pipeline - Supply Chain Disruption Intelligence

What this does:
1. Named Entity Recognition (NER) - Extract ports, carriers, locations
2. Sentiment Analysis - Measure disruption severity
3. Zero-Shot Classification - Categorize disruption type

Why we need this:
- Turns unstructured news → structured risk signals
- Powers the "What's happening now" section of risk explanations
- Feeds into historical pattern matching (ChromaDB tomorrow)

HuggingFace Tasks Used:
- Task #2: Token Classification (NER)
- Task #3: Text Classification (Sentiment)
- Task #4: Zero-Shot Classification

All models are pre-trained (no fine-tuning needed for MVP).
"""

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification
)
import torch
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

class NewsAnalyzer:
    """
    Analyzes supply chain news headlines using 3 HuggingFace models.
    
    Models used:
    1. NER: dslim/bert-base-NER (general entity extraction)
    2. Sentiment: distilbert-base-uncased-finetuned-sst-2-english
    3. Zero-shot: facebook/bart-large-mnli
    """
    
    def __init__(self):
        """Initialize all 3 models. Takes ~30 seconds on first run."""
        print("🔧 Initializing News Analyzer...")
        
        # Model 1: Named Entity Recognition
        print("   Loading NER model...")
        self.ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple"  # Combines word pieces
        )
        
        # Model 2: Sentiment Analysis
        print("   Loading Sentiment model...")
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # Model 3: Zero-Shot Classification
        print("   Loading Zero-shot classifier...")
        self.classifier_pipeline = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Supply chain disruption categories
        self.disruption_categories = [
            "Weather Event",
            "Port Congestion",
            "Geopolitical Conflict",
            "Labor Strike",
            "Carrier Failure",
            "Infrastructure Damage",
            "Demand Surge"
        ]
        
        print("✅ News Analyzer ready!\n")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from headline.
        
        Example:
        Input: "Maersk vessels delayed at Shanghai port due to typhoon"
        Output: {
            "locations": ["Shanghai"],
            "organizations": ["Maersk"],
            "events": ["typhoon"]
        }
        """
        ner_results = self.ner_pipeline(text)
        
        entities = {
            "locations": [],
            "organizations": [],
            "persons": [],
            "misc": []
        }
        
        for entity in ner_results:
            entity_type = entity['entity_group']
            entity_text = entity['word']
            
            if entity_type == 'LOC':
                entities['locations'].append(entity_text)
            elif entity_type == 'ORG':
                entities['organizations'].append(entity_text)
            elif entity_type == 'PER':
                entities['persons'].append(entity_text)
            elif entity_type == 'MISC':
                entities['misc'].append(entity_text)
        
        # Remove duplicates while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Measure sentiment (disruption severity).
        
        Returns:
        {
            "label": "NEGATIVE",  # POSITIVE or NEGATIVE
            "score": 0.98,        # Confidence (0-1)
            "risk_signal": 0.98   # -1 to +1 (negative = high risk)
        }
        
        Note: For supply chains, NEGATIVE news = high risk
        """
        result = self.sentiment_pipeline(text)[0]
        
        # Convert to risk signal
        # NEGATIVE sentiment = positive risk signal
        label = result['label']
        score = result['score']
        
        if label == 'NEGATIVE':
            risk_signal = score  # Already positive
        else:  # POSITIVE
            risk_signal = -score  # Negative risk (good news)
        
        return {
            "label": label,
            "score": score,
            "risk_signal": risk_signal
        }
    
    def categorize_disruption(self, text: str) -> List[Dict[str, float]]:
        """
        Classify disruption type using zero-shot learning.
        
        No training data needed - model infers from text.
        
        Returns:
        [
            {"category": "Weather Event", "confidence": 0.96},
            {"category": "Port Congestion", "confidence": 0.68},
            ...
        ]
        """
        result = self.classifier_pipeline(
            text,
            candidate_labels=self.disruption_categories,
            multi_label=True  # Can have multiple categories
        )
        
        # Format results
        categories = []
        for label, score in zip(result['labels'], result['scores']):
            if score > 0.3:  # Only include confident predictions
                categories.append({
                    "category": label,
                    "confidence": round(score, 3)
                })
        
        return categories
    
    def summarize(self, text: str, max_length: int = 50) -> str:
        """
        Summarize long text into concise alert.
        
        HuggingFace Task #6: Summarization
        Model: sshleifer/distilbart-cnn-12-6 (smaller, faster)
        
        Args:
            text: Long article or report
            max_length: Maximum words in summary
        
        Returns:
            Concise one-line summary
        """
        
        # Load summarizer on first use (lazy loading)
        if not hasattr(self, 'summarizer'):
            print("   Loading summarization model (first time only)...")
            # Use text-generation pipeline with BART
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            model_name = "sshleifer/distilbart-cnn-12-6"
            self.sum_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.sum_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Already short, no need to summarize
        if len(text.split()) < 30:
            return text
        
        # Tokenize
        inputs = self.sum_tokenizer(
            text,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        )
        
        # Generate summary
        summary_ids = self.sum_model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=20,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        # Decode
        summary = self.sum_tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True
        )
        
        return summary
    
    def analyze(self, headline: str) -> Dict:
        """
        Full analysis pipeline - runs all 3 tasks.
        
        Example:
        >>> analyzer = NewsAnalyzer()
        >>> result = analyzer.analyze("Shanghai port operations reduced 40% due to Typhoon Saola")
        >>> print(result)
        {
            "headline": "Shanghai port operations...",
            "entities": {"locations": ["Shanghai"], ...},
            "sentiment": {"label": "NEGATIVE", "risk_signal": 0.98},
            "categories": [{"category": "Weather Event", "confidence": 0.96}]
        }
        """
        print(f"\n📰 Analyzing: '{headline[:60]}...'")
        
        # Run all 3 models
        entities = self.extract_entities(headline)
        sentiment = self.analyze_sentiment(headline)
        categories = self.categorize_disruption(headline)
        
        result = {
            "headline": headline,
            "entities": entities,
            "sentiment": sentiment,
            "categories": categories
        }
        
        # Print summary
        print(f"   Entities: {entities['locations']} (locations), {entities['organizations']} (orgs)")
        print(f"   Sentiment: {sentiment['label']} (risk: {sentiment['risk_signal']:.2f})")
        print(f"   Primary category: {categories[0]['category'] if categories else 'Unknown'}")
        
        return result

def main():
    """Demo: Analyze sample supply chain headlines."""
    
    # Initialize analyzer
    analyzer = NewsAnalyzer()
    
    # Sample headlines (mix of real and synthetic)
    headlines = [
        "Shanghai port operations reduced 40% due to Typhoon Saola affecting Maersk and MSC shipments",
        "Suez Canal blockage: Ever Given container ship stuck, 400 vessels delayed",
        "Los Angeles port congestion reaches 5-year high as demand surges",
        "Panama Canal water levels dropping, vessel restrictions implemented",
        "Maersk announces new Asia-Europe route to avoid Red Sea disruptions"
    ]
    
    print("=" * 70)
    print("NEWS ANALYSIS PIPELINE - DEMO")
    print("=" * 70)
    
    results = []
    for headline in headlines:
        result = analyzer.analyze(headline)
        results.append(result)
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY OF ANALYSIS")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['headline'][:60]}...")
        print(f"   Risk Signal: {result['sentiment']['risk_signal']:.2f}")
        print(f"   Category: {result['categories'][0]['category'] if result['categories'] else 'N/A'}")
        
        if result['entities']['locations']:
            print(f"   Affected Ports: {', '.join(result['entities']['locations'])}")
        if result['entities']['organizations']:
            print(f"   Carriers: {', '.join(result['entities']['organizations'])}")
    
    print("\n✅ Analysis complete!")
    print(f"💾 Analyzed {len(headlines)} headlines using 3 HuggingFace models\n")

if __name__ == "__main__":
    main()