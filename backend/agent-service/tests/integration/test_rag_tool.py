import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.rag_tool import RAGTool

async def test_rag_tool():
    """Test RAGTool functionality"""
    tool = RAGTool()
    
    # Test query
    query = "What is Monthly maintenance fee?"
    
    print(f"Testing query: {query}\n")
    
    # Test 1: search_policy
    print("=" * 50)
    print("Test 1: search_policy()")
    print("=" * 50)
    try:
        results = await tool.search_policy(query)
        print(f"✓ Success! Found {results.get('count', 0)} results")
        print(f"Query: {results.get('query')}")
        if results.get('results'):
            print(f"\nFirst result:")
            print(f"  Title: {results['results'][0].get('title')}")
            print(f"  Similarity: {results['results'][0].get('similarity_distance')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n")
    
    # Test 2: get_policy_context
    print("=" * 50)
    print("Test 2: get_policy_context()")
    print("=" * 50)
    try:
        context = await tool.get_policy_context(query)
        print(f"✓ Success!")
        print(f"Context length: {len(context)} characters")
        print(f"\nContext preview:\n{context}")

    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rag_tool())