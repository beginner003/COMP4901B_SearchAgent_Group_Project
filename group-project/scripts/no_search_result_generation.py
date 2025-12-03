import sys
import os

# Add parent directory to path so we can import from src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now we can import from src
from src.agent import NoSearchAgent
from src.utils import read_jsonl, write_jsonl


def main():
    agent = NoSearchAgent(max_tokens=32)
    data = read_jsonl("data/nq_test_100.jsonl")
    
    predictions = []
    for item in data:
        print(f"Answering question: {item['question']}")
        answer = agent.answer_question(item["question"])
        print(f"Answer: {answer}")
        print("="*50)
        prediction = {
            "id": item["id"],
            "question": item["question"],
            "answers": item["answers"],
            "llm_response": answer
        }
        predictions.append(prediction)
        

    write_jsonl("results/nosearch/trial2/predictions_nosearch.jsonl", predictions)

if __name__ == "__main__":
    main()