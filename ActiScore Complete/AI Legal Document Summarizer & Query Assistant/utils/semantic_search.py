from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os

class LegalSemanticSearch:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.document_metadata = []
        self.index_path = 'faiss_index/legal_docs.index'
        self.metadata_path = 'faiss_index/legal_docs_metadata.pkl'
        
        self._load_index()
    
    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.documents, self.document_metadata = pickle.load(f)
            except Exception as e:
                print(f"Error loading existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        self.index = faiss.IndexFlatIP(384)  # Dimension for all-MiniLM-L6-v2
        self.documents = []
        self.document_metadata = []
    
    def _save_index(self):
        os.makedirs('faiss_index', exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump((self.documents, self.document_metadata), f)
    
    def add_document(self, text, filename):
        # Split document into chunks for better search
        chunks = self._split_document(text)
        
        for i, chunk in enumerate(chunks):
            embedding = self.model.encode([chunk])
            embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
            
            self.index.add(embedding.astype('float32'))
            self.documents.append(chunk)
            self.document_metadata.append({
                'filename': filename,
                'chunk_id': i,
                'total_chunks': len(chunks)
            })
        
        self._save_index()
    
    def _split_document(self, text, max_chunk_size=512):
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) <= max_chunk_size:
                current_chunk.append(word)
                current_size += len(word) + 1
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def search(self, query, top_k=3):
        if self.index.ntotal == 0:
            return []
        
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    'content': self.documents[idx],
                    'score': float(score),
                    'metadata': self.document_metadata[idx]
                })
        
        return results