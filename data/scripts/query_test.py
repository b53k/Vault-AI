import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from vectorize import mean_pooling

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model.eval()

query = "Monthly maintenance fee?"

encoded_input = tokenizer(query, padding=True, truncation=True, return_tensors='pt')

with torch.no_grad():
    model_output = model(**encoded_input)

sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

# convert to pgvector string format
embedding_list = sentence_embeddings[0].cpu().numpy().tolist()
pgvector_string = '[' + ','.join(str(val) for val in embedding_list) + ']'
print (pgvector_string)
