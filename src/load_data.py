
from sentence_transformers import SentenceTransformer
import json
import time
import uuid
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from db_loader import load_data 
from embedding import process_products_with_chunking


def load_and_process_data():
    """
    Load product data, chunk text, generate embeddings, and store vectors in Qdrant
    """
    # 1. Load model
    print("Loading sentence-transformer model...")
    model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")
    print("Model loaded.\n")
    # Load product data
    # print("Loading product data from MongoDB...")
    # products = load_data()

    # print(f"Loaded {len(products)} products.")
    # 2. Load product data
    print("Loading product data...")
    with open('data/products_info.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products.\n")

    # 3. Chunk and embed
    print("Chunking and encoding products...")
    start_time = time.time()
    chunked_documents = process_products_with_chunking(
        products=products,
        model=model,
        chunk_size=300,
        overlap=50
    )
    end_time = time.time()
    print(f"Created {len(chunked_documents)} chunks in {end_time - start_time:.2f} seconds.\n")

    # 4. Save backup
    with open('data/chunked_documents.json', 'w', encoding='utf-8') as f:
        json.dump(chunked_documents, f, ensure_ascii=False, indent=4)
    print("Saved chunked documents to 'data/chunked_documents.json'.\n")

    # 5. Connect to Qdrant
    print("Connecting to Qdrant...")
    client = QdrantClient(url="http://20.205.16.72:6333", timeout=60.0)
    print("Connected to Qdrant.\n")

    # 6. Create or reset collection
    if client.collection_exists("chunked_documents"):
        print("Collection 'chunked_documents' exists. Deleting...")
        client.delete_collection("chunked_documents")
        print("Deleted old collection.\n")

    client.create_collection(
        collection_name="chunked_documents",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        shard_number=1
    )
    print("Created new collection.\n")

    # 7. Prepare and upload
    BATCH_SIZE = 100
    print(f"Uploading vectors to Qdrant in batches of {BATCH_SIZE}...")

    for i in tqdm(range(0, len(chunked_documents), BATCH_SIZE), desc="Uploading"):
        batch_docs = chunked_documents[i:i + BATCH_SIZE]
        batch_points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=doc["values"],
                payload=doc["metadata"]
            )
            for doc in batch_docs
        ]
        client.upsert(collection_name="chunked_documents", points=batch_points)

    print("Upload completed successfully.")


if __name__ == "__main__":
    load_and_process_data()