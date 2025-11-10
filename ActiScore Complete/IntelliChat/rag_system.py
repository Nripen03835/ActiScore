import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import openai
from config import Config

class RAGSystem:
    def __init__(self):
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index = None
        self.documents = []
        self.openai_client = None
        
        # Initialize OpenAI client only if API key is provided
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'your-openai-key-here':
            try:
                self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                print("OpenAI client initialized successfully")
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.openai_client = None
        else:
            print("Using local response generation (no OpenAI API key provided)")
        
    def load_documents(self):
        """Load all sample documents and create embeddings"""
        all_docs = []
        
        # Load attendance data
        try:
            with open('database/sample_data/attendance.json', 'r') as f:
                attendance_data = json.load(f)
                for record in attendance_data:
                    doc_text = f"Attendance: Student {record['student_name']} was {record['status']} on {record['date']} for {record['hours']} hours"
                    all_docs.append({
                        'text': doc_text,
                        'metadata': {'type': 'attendance', 'source': 'attendance.json'}
                    })
        except FileNotFoundError:
            print("Attendance data not found")
        
        # Load summaries
        try:
            with open('database/sample_data/summaries.json', 'r') as f:
                summaries_data = json.load(f)
                for summary in summaries_data:
                    doc_text = f"Summary: {summary['title']} - {summary['content']}"
                    all_docs.append({
                        'text': doc_text,
                        'metadata': {'type': 'summary', 'source': 'summaries.json'}
                    })
        except FileNotFoundError:
            print("Summaries data not found")
        
        # Load analytics
        try:
            with open('database/sample_data/analytics.json', 'r') as f:
                analytics_data = json.load(f)
                for analytic in analytics_data:
                    doc_text = f"Analytics: {analytic['metric']} is {analytic['value']} - {analytic['insights']}"
                    all_docs.append({
                        'text': doc_text,
                        'metadata': {'type': 'analytics', 'source': 'analytics.json'}
                    })
        except FileNotFoundError:
            print("Analytics data not found")
        
        # Load research papers
        try:
            with open('database/sample_data/research.json', 'r') as f:
                research_data = json.load(f)
                for paper in research_data:
                    doc_text = f"Research: {paper['title']} by {', '.join(paper['authors'])} - {paper['abstract']}"
                    all_docs.append({
                        'text': doc_text,
                        'metadata': {'type': 'research', 'source': 'research.json'}
                    })
        except FileNotFoundError:
            print("Research data not found")
        
        self.documents = all_docs
        print(f"Loaded {len(all_docs)} documents")
        return all_docs
    
    def build_index(self):
        """Build FAISS index from documents"""
        try:
            if not self.documents:
                self.load_documents()
            
            if not self.documents:
                print("No documents to index")
                return
            
            texts = [doc['text'] for doc in self.documents]
            embeddings = self.embedding_model.encode(texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings).astype('float32'))
            
            # Save index
            os.makedirs('data', exist_ok=True)
            faiss.write_index(self.index, Config.FAISS_INDEX_PATH)
            print(f"FAISS index built with {len(self.documents)} documents")
            
        except Exception as e:
            print(f"Error building FAISS index: {e}")
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            if self.index is None:
                if os.path.exists(Config.FAISS_INDEX_PATH):
                    self.index = faiss.read_index(Config.FAISS_INDEX_PATH)
                else:
                    self.build_index()
            
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'document': self.documents[idx],
                        'score': float(distances[0][i])
                    })
            
            return results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using OpenAI or local fallback"""
        if not context_docs:
            return "I couldn't find relevant information in the available data. Please try asking about attendance, summaries, analytics, or research papers."
        
        context = "\n".join([doc['document']['text'] for doc in context_docs])
        
        if self.openai_client and not Config.USE_LOCAL_LLM:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are IntelliChat, a helpful assistant that answers questions based on the provided context. Be concise and accurate."},
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {e}")
        
        # Local fallback response
        return self._local_response(query, context)
    
    def _local_response(self, query: str, context: str) -> str:
        """Simple local response generation"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['attendance', 'present', 'absent']):
            return f"Based on attendance records: {context[:200]}..."
        elif any(word in query_lower for word in ['summary', 'report']):
            return f"Here's relevant summary information: {context[:200]}..."
        elif any(word in query_lower for word in ['analytics', 'metric', 'performance']):
            return f"Analytics data shows: {context[:200]}..."
        elif any(word in query_lower for word in ['research', 'paper', 'study']):
            return f"Research information: {context[:200]}..."
        else:
            return f"I found this information relevant to your query: {context[:300]}..."
    
    def query(self, question: str) -> str:
        """Main query method"""
        relevant_docs = self.search(question)
        response = self.generate_response(question, relevant_docs)
        return response