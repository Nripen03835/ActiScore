import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ResearchSummarizer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        return text
    
    def summarize(self, text, summary_ratio=0.3):
        # Tokenize sentences
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 5:
            return " ".join(sentences)
        
        # Preprocess text for TF-IDF
        preprocessed_text = self.preprocess_text(text)
        
        # Calculate TF-IDF scores
        vectorizer = TfidfVectorizer(stop_words=list(self.stop_words))
        tfidf_matrix = vectorizer.fit_transform([preprocessed_text])
        feature_names = vectorizer.get_feature_names_out()
        
        # Calculate sentence scores
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            words = word_tokenize(self.preprocess_text(sentence))
            score = 0
            word_count = 0
            for word in words:
                if word in feature_names:
                    word_idx = list(feature_names).index(word)
                    score += tfidf_matrix[0, word_idx]
                    word_count += 1
            if word_count > 0:
                sentence_scores[i] = score / word_count
        
        # Select top sentences
        num_sentences = max(2, int(len(sentences) * summary_ratio))
        top_sentences = sorted(sentence_scores.items(), 
                              key=lambda x: x[1], reverse=True)[:num_sentences]
        top_sentences = sorted([s[0] for s in top_sentences])
        
        # Generate summary
        summary = ' '.join([sentences[i] for i in top_sentences])
        return summary
    
    def extract_contributions(self, text):
        # Look for contribution-related sections
        contributions = []
        
        # Common patterns for contributions
        patterns = [
            r'contribution[s]?[:\s]+([^\.]+\.)',
            r'we propose[s]?[:\s]+([^\.]+\.)',
            r'our approach[:\s]+([^\.]+\.)',
            r'key innovation[s]?[:\s]+([^\.]+\.)',
            r'main contribution[s]?[:\s]+([^\.]+\.)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contributions.extend(matches)
        
        # If no specific patterns found, use important sentences
        if not contributions:
            sentences = sent_tokenize(text)
            # Look for sentences that might indicate contributions
            contribution_keywords = ['propose', 'develop', 'introduce', 'contribution', 
                                   'innovation', 'novel', 'new method', 'framework']
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in contribution_keywords):
                    if len(sentence.split()) > 5:  # Avoid very short sentences
                        contributions.append(sentence.strip())
        
        # Limit to top 5 contributions
        return contributions[:5]