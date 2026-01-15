import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List
import numpy as np

class EmbeddingsService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()


    def mean_pooling(self, model_output, attention_mask):
        """Mean Pooling for Hugging Face Transformers"""
        
        token_embeddings = model_output[0] #First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    


    def generate_embedding(self, text: str) -> List[float]:
        encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(self.device)

        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        sentence_embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        
        return sentence_embeddings[0].cpu().numpy().tolist()


    def embedding_to_pgvector_string(self, embedding: List[float]) -> str:
        """Convert embedding tensor to pgvector string format [v1, v2, v3, ...]"""
        pgvector_string = '[' + ','.join(str(val) for val in embedding) + ']'
        return pgvector_string


embeddings_service = EmbeddingsService()