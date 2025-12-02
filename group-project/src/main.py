import argparse
import json
from typing import Optional
from tqdm import tqdm
from agent import agent_loop, generate_no_search
from agent import agent_loop_with_trajectory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--mode", choices=["interactive", "no_search", "search_only", "browse"], default="interactive")
    args = parser.parse_args()

    if args.mode == "interactive":
        try:
            question = input("Enter a question: ").strip()
        except EOFError:
            question = "What is the capital of France?"
        if not question:
            question = "What is the capital of France?"
        answer = agent_loop(question, allowed_tools=["search", "browse", "answer"])
        print(answer)
        return

    if not args.dataset or not args.output:
        print("Missing --dataset or --output for batch mode")
        return
    
    traj_out_path = None
    with open(args.dataset, "r", encoding="utf-8") as f_in, open(args.output, "w", encoding="utf-8") as f_out:
        if args.mode in ("search_only", "browse"):
            if args.mode == "search_only":
                traj_out_path = args.output.replace("predictions_search.jsonl", "agent_trajectories_search_only.jsonl")
            else:
                traj_out_path = args.output.replace("predictions_browse.jsonl", "agent_trajectories.jsonl")
            traj_f = open(traj_out_path, "w", encoding="utf-8")
        else:
            traj_f = None
        for line in tqdm(f_in, desc="Generating"):
            ex = json.loads(line)
            q = ex["question"]
            if args.mode == "no_search":
                resp = generate_no_search(q)
                rec = {"id": ex["id"], "question": ex["question"], "answers": ex.get("answers", []), "llm_response": resp}
                f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            elif args.mode == "search_only":
                res = agent_loop_with_trajectory(q, allowed_tools=["search", "answer"])
                resp = res["final_answer"]
                rec = {"id": ex["id"], "question": ex["question"], "answers": ex.get("answers", []), "llm_response": resp}
                f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if traj_f:
                    traj_rec = {
                        "id": ex["id"],
                        "question": ex["question"],
                        "ground_truths": ex.get("answers", []),
                        "trajectory": {
                            "question": ex["question"],
                            "steps": res.get("steps", []),
                            "final_answer": resp,
                            "total_search_steps": res.get("total_search_steps", 0),
                        },
                    }
                    traj_f.write(json.dumps(traj_rec, ensure_ascii=False) + "\n")
            else:
                res = agent_loop_with_trajectory(q, allowed_tools=["search", "browse", "answer"])
                resp = res["final_answer"]
                rec = {"id": ex["id"], "question": ex["question"], "answers": ex.get("answers", []), "llm_response": resp}
                f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if traj_f:
                    traj_rec = {
                        "id": ex["id"],
                        "question": ex["question"],
                        "ground_truths": ex.get("answers", []),
                        "trajectory": {
                            "question": ex["question"],
                            "steps": res.get("steps", []),
                            "final_answer": resp,
                            "total_search_steps": res.get("total_search_steps", 0),
                        },
                    }
                    traj_f.write(json.dumps(traj_rec, ensure_ascii=False) + "\n")
        if traj_f:
            traj_f.close()


if __name__ == "__main__":
    main()
