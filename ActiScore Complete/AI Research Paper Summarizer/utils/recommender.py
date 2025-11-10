import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import re

class PaperRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.svd = TruncatedSVD(n_components=100)
        self.papers = []
        self.paper_vectors = None
    
    def preprocess_text(self, text):
        # Combine title, abstract, and keywords for better representation
        if isinstance(text, dict):
            # If it's a paper dictionary
            content_parts = []
            if 'title' in text:
                content_parts.append(text['title'])
            if 'abstract' in text:
                content_parts.append(text['abstract'])
            if 'keywords' in text:
                content_parts.extend(text['keywords'])
            text = ' '.join(content_parts)
        
        # Clean text
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        text = text.lower()
        return text
    
    def fit(self, papers):
        self.papers = papers
        
        # Preprocess all papers
        processed_texts = [self.preprocess_text(paper) for paper in papers]
        
        # Create TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
        
        # Apply dimensionality reduction
        self.paper_vectors = self.svd.fit_transform(tfidf_matrix)
    
    def recommend_similar(self, query_text, top_k=5):
        if self.paper_vectors is None:
            raise ValueError("Recommender not fitted with papers data")
        
        # Preprocess query
        processed_query = self.preprocess_text(query_text)
        
        # Transform query to same vector space
        query_vector = self.vectorizer.transform([processed_query])
        query_vector_reduced = self.svd.transform(query_vector)
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector_reduced, self.paper_vectors)[0]
        
        # Get top similar papers
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        recommended_papers = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                paper = self.papers[idx].copy()
                paper['similarity_score'] = float(similarities[idx])
                recommended_papers.append(paper)
        
        return recommended_papers
    
    def recommend_by_keywords(self, keywords, top_k=5):
        return self.recommend_similar(keywords, top_k)