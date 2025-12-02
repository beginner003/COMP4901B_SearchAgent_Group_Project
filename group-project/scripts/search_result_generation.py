import sys
import os

# Add parent directory to path so we can import from src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now we can import from src
from src.agent import SearchAgent
from src.utils import read_jsonl, write_jsonl


def main():
    agent = SearchAgent(max_tokens=32, max_steps=10, include_browse=False)
    data = read_jsonl("data/nq_test_100.jsonl")
    
    predictions = []
    for item in data:
        print(f"Answering question: {item['question']}")
        result = agent.agent_loop(item["question"])
        trajectory  = agent.print_trajectory(result, save_as_json=True)
        prediction = {
            "id": item["id"],
            "question": item["question"],
            "ground_truths": item["answers"],
            "trajectory": trajectory
        }
        predictions.append(prediction)
        

    write_jsonl("results/search/trial1/predictions_search_no_browse.jsonl", predictions)

if __name__ == "__main__":
    main()