import sys
sys.path.append('src')

from utils.embeddings_manager import EmbeddingsManager

def main():
    print("Creating manager...")
    manager = EmbeddingsManager()
    print("\nSearching for similar questions...")
    result = manager.find_similar_questions('איך לשפר מכירות?', threshold=0.5)
    print(f"\nFound {len(result)} matches:")
    for q, a, score in result:
        print(f"\nScore: {score:.3f}")
        print(f"Question: {q}")
        print(f"Answer: {a}")

if __name__ == '__main__':
    main() 