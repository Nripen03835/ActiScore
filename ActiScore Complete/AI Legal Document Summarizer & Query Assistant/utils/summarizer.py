from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from threading import Lock
import time

class LegalSummarizer:
    def __init__(self):
        self.model_name = "facebook/bart-large-cnn"
        self.device = 0 if torch.cuda.is_available() else -1  # Use GPU if available
        
        print("Loading summarization model...")
        start_time = time.time()
        
        # Use a smaller, faster model for production
        try:
            # Try to use a smaller, faster model first
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                device=self.device,
                framework="pt"
            )
        except:
            # Fallback to basic model
            self.summarizer = pipeline(
                "summarization",
                device=self.device
            )
        
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f} seconds")
        
        self.lock = Lock()  # For thread safety
        
    def summarize(self, text, max_length=300, min_length=100):
        """
        Optimized summarization with faster processing
        """
        if not text or len(text.strip()) < 50:
            return "Text too short to summarize."
        
        start_time = time.time()
        
        # Pre-process text to remove excessive whitespace
        text = self._preprocess_text(text)
        
        # For very long documents, use extractive summarization first
        if len(text) > 2000:
            summary = self._fast_summarize_large_text(text, max_length, min_length)
        else:
            summary = self._summarize_with_fallback(text, max_length, min_length)
        
        processing_time = time.time() - start_time
        print(f"Summarization completed in {processing_time:.2f} seconds")
        
        return summary
    
    def _preprocess_text(self, text):
        """Clean and preprocess text for faster processing"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove very short paragraphs
        paragraphs = [p for p in text.split('\n') if len(p.strip()) > 10]
        text = '\n'.join(paragraphs)
        
        return text[:10000]  # Limit text length for faster processing
    
    def _fast_summarize_large_text(self, text, max_length, min_length):
        """
        Fast summarization for large documents using hybrid approach
        """
        # First, extract important sentences
        important_sentences = self._extract_key_sentences(text, num_sentences=10)
        reduced_text = ' '.join(important_sentences)
        
        # Then use abstractive summarization on the reduced text
        if len(reduced_text) > 1500:
            reduced_text = reduced_text[:1500]  # Further limit for speed
        
        return self._summarize_with_fallback(reduced_text, max_length, min_length)
    
    def _extract_key_sentences(self, text, num_sentences=10):
        """
        Fast extractive summarization to reduce text size
        """
        sentences = text.split('. ')
        if len(sentences) <= num_sentences:
            return sentences
        
        # Simple sentence scoring based on position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 10:  # Skip very short sentences
                continue
                
            score = 0
            # Prefer sentences at the beginning (often contain main ideas)
            if i < len(sentences) * 0.3:  # First 30% of sentences
                score += 2
            elif i > len(sentences) * 0.7:  # Last 30% of sentences (conclusions)
                score += 1
                
            # Prefer medium-length sentences
            sentence_length = len(sentence.split())
            if 10 <= sentence_length <= 30:
                score += 1
                
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_sentences[:num_sentences]]
    
    def _summarize_with_fallback(self, text, max_length, min_length):
        """
        Try abstractive summarization with fallback to extractive
        """
        try:
            with self.lock:  # Ensure thread safety
                summary = self.summarizer(
                    text,
                    max_length=min(max_length, 300),  # Reduced max length for speed
                    min_length=min(min_length, 100),  # Reduced min length for speed
                    do_sample=False,
                    truncation=True,
                    no_repeat_ngram_size=2  # Prevent repetition for faster processing
                )
                return summary[0]['summary_text']
                
        except Exception as e:
            print(f"Abstractive summarization failed, using extractive: {e}")
            return self._fast_extractive_summary(text)
    
    def _fast_extractive_summary(self, text, ratio=0.3):
        """
        Very fast extractive summarization as fallback
        """
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        if not sentences:
            return text[:500]  # Just return first 500 chars as fallback
        
        num_sentences = max(1, int(len(sentences) * ratio))
        
        # Take first, middle, and last sentences for better coverage
        if len(sentences) <= num_sentences:
            return '. '.join(sentences) + '.'
        
        selected_indices = set()
        
        # Always include first sentence
        selected_indices.add(0)
        
        # Include some middle sentences
        middle_start = len(sentences) // 3
        for i in range(middle_start, middle_start + (num_sentences - 2)):
            if i < len(sentences):
                selected_indices.add(i)
        
        # Always include last sentence
        selected_indices.add(len(sentences) - 1)
        
        # Fill remaining slots with highest scoring sentences
        remaining_slots = num_sentences - len(selected_indices)
        if remaining_slots > 0:
            # Simple scoring based on sentence length (medium sentences are often important)
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                if i not in selected_indices:
                    words = len(sentence.split())
                    score = 1.0 / abs(words - 20)  # Prefer sentences around 20 words
                    scored_sentences.append((i, score))
            
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            for i in range(min(remaining_slots, len(scored_sentences))):
                selected_indices.add(scored_sentences[i][0])
        
        # Return sentences in original order
        selected_sentences = [sentences[i] for i in sorted(selected_indices)]
        return '. '.join(selected_sentences) + '.'