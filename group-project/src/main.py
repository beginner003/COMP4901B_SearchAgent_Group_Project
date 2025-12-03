import argparse
import json
from typing import Optional
from tqdm import tqdm
from agent import agent_loop, generate_no_search
from agent import agent_loop_with_trajectory
from tools import gmail_send_email, search_tool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--mode", choices=["interactive", "no_search", "search_only", "browse", "meeting_email", "meeting_agent"], default="interactive")
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--attendees", type=str, default=None, help="Comma-separated emails for meeting notifications")
    parser.add_argument("--calendar_link", type=str, default=None)
    parser.add_argument("--notion_link", type=str, default=None)
    parser.add_argument("--suggestion_query", type=str, default=None)
    parser.add_argument("--traj_out", type=str, default=None)
    parser.add_argument("--request", type=str, default=None)
    parser.add_argument("--timezone", type=str, default="UTC")
    parser.add_argument("--calendar_id", type=str, default=None)
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

    if args.mode == "meeting_agent":
        if not args.request:
            print("Missing --request for meeting_agent mode")
            return
        attendees = [e.strip() for e in (args.attendees or "").split(",") if e.strip()]
        steps = []
        from src.utils import call_deepseek, load_config
        from src.prompts import REAL_WORLD_AGENT_SYSTEM_PROMPT
        cfg = load_config()
        parse_msgs = [
            {"role": "system", "content": REAL_WORLD_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": "Extract structured JSON from the request with keys: title (string), date (YYYY-MM-DD), time (HH:MM), attendees (list of emails), topics (list of strings). Return only JSON."},
            {"role": "user", "content": args.request},
        ]
        parse_resp = call_deepseek(messages=parse_msgs, config=cfg, temperature=0.2, max_tokens=300)
        parse_text = parse_resp.choices[0].message.content
        try:
            parsed = json.loads(parse_text)
        except Exception:
            parsed = {"title": "Team Meeting", "date": None, "time": None, "attendees": attendees, "topics": []}
        steps.append({"step_number": 1, "action": "parse", "parsed": parsed})
        agenda_msgs = [
            {"role": "system", "content": REAL_WORLD_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": "Create a concise agenda with sections: Title, Discussion Points (bulleted), Action Items (bulleted). Use topics."},
            {"role": "user", "content": json.dumps({"title": parsed.get("title"), "topics": parsed.get("topics", [])}, ensure_ascii=False)},
        ]
        agenda_resp = call_deepseek(messages=agenda_msgs, config=cfg, temperature=0.3, max_tokens=600)
        agenda_text = agenda_resp.choices[0].message.content
        steps.append({"step_number": 2, "action": "agenda", "length": len(agenda_text)})
        title = parsed.get("title") or (args.subject or "Team Meeting")
        date = parsed.get("date")
        time_str = parsed.get("time")
        tz = args.timezone
        if date and time_str:
            start_iso = f"{date}T{time_str}:00"
        else:
            import re
            from datetime import datetime, timedelta
            req = args.request.lower()
            m = re.search(r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2})(?:\:(\d{2}))?\s*(am|pm)?", req)
            start_iso = None
            if m:
                target_day = m.group(1)
                hour = int(m.group(2))
                minute = int(m.group(3) or 0)
                ampm = m.group(4)
                if ampm == "pm" and hour < 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
                weekday_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
                target_idx = weekday_map.get(target_day)
                now = datetime.now()
                delta_days = (target_idx - now.weekday() + 7) % 7
                delta_days = 7 if delta_days == 0 else delta_days
                next_day = now + timedelta(days=delta_days)
                start_iso = next_day.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat(timespec="seconds")
        def add_minutes(iso: str, minutes: int) -> str:
            from datetime import datetime, timedelta
            try:
                dt = datetime.fromisoformat(iso)
                return (dt + timedelta(minutes=minutes)).isoformat(timespec="seconds")
            except Exception:
                return iso
        end_iso = add_minutes(start_iso, 60) if start_iso else None
        from src.tools import calendar_create_event, create_notion_page, gmail_send_email, search_tool
        cal_result = {"created": False}
        if start_iso and end_iso:
            cal_result = calendar_create_event(title, agenda_text, start_iso, end_iso, parsed.get("attendees") or attendees, calendar_id=args.calendar_id, timezone=tz)
        steps.append({"step_number": 3, "action": "calendar_create", "result": cal_result})
        notion_link = None
        # Prepare suggestions before creating Notion children so they can be included
        suggest_query = args.suggestion_query or (f"best practices for {parsed.get('topics')[0]}" if parsed.get("topics") else None)
        suggestions_text = None
        if suggest_query:
            sres = search_tool(suggest_query)
            suggestions_text = sres.get("text") if isinstance(sres, dict) else str(sres)
            steps.append({"step_number": 5, "action": "search", "query": suggest_query, "log": sres.get("log") if isinstance(sres, dict) else {}})

        from src.utils import load_config as _lc
        dbid = _lc().get("NOTION_DATABASE_ID")
        if dbid:
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Agenda"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": agenda_text[:1900]}}]}
                }
            ]
            if cal_result.get("htmlLink"):
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Calendar: {cal_result.get('htmlLink')}"}}]}
                })
            if suggestions_text:
                children.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Resources"}}]}
                })
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": suggestions_text[:1900]}}]}
                })
            notion_res = create_notion_page(
                dbid,
                title,
                meeting_date=date or None,
                status="Scheduled",
                attendees=(parsed.get("attendees") or attendees),
                discussion_topics=", ".join(parsed.get("topics", [])),
                action_items="",
                children=children
            )
            notion_link = notion_res.get("url")
            steps.append({"step_number": 4, "action": "notion_update", "result": notion_res})
        else:
            steps.append({"step_number": 4, "action": "notion_update", "error": "Missing NOTION_DATABASE_ID"})
        # suggestions_text already computed above, use in email body if present
        body_parts = []
        if cal_result.get("htmlLink"):
            body_parts.append(f"Calendar: {cal_result.get('htmlLink')}")
        if notion_link:
            body_parts.append(f"Notion: {notion_link}")
        if suggestions_text:
            body_parts.append("Resources:\n" + suggestions_text)
        body_parts.append(agenda_text)
        body_text = "\n\n".join(body_parts)
        send_res = gmail_send_email(parsed.get("attendees") or attendees, title, body_text)
        steps.append({"step_number": 6, "action": "gmail_send", "recipients": (parsed.get("attendees") or attendees), "subject": title, "sent": bool(send_res.get("sent")), "error": send_res.get("error")})
        print(send_res)
        if args.traj_out:
            rec = {"mode": "meeting_agent", "request": args.request, "steps": steps, "result": send_res}
            with open(args.traj_out, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return

    if args.mode == "meeting_email":
        if not args.subject or not args.attendees:
            print("Missing --subject or --attendees for meeting_email mode")
            return
        attendees = [e.strip() for e in args.attendees.split(",") if e.strip()]
        steps = []
        body_parts = []
        if args.calendar_link:
            body_parts.append(f"Calendar: {args.calendar_link}")
            steps.append({"step_number": 1, "action": "compose", "included_calendar_link": True})
        if args.notion_link:
            body_parts.append(f"Notion: {args.notion_link}")
            steps.append({"step_number": len(steps)+1, "action": "compose", "included_notion_link": True})
        if args.suggestion_query:
            search_res = search_tool(args.suggestion_query)
            suggestions_text = search_res.get("text") if isinstance(search_res, dict) else str(search_res)
            body_parts.append("Resources:\n" + suggestions_text)
            steps.append({"step_number": len(steps)+1, "action": "search", "query": args.suggestion_query, "log": search_res.get("log") if isinstance(search_res, dict) else {}})
        body_text = "\n\n".join(body_parts) if body_parts else "Meeting scheduled."
        send_res = gmail_send_email(attendees, args.subject, body_text)
        steps.append({"step_number": len(steps)+1, "action": "gmail_send", "recipients": attendees, "subject": args.subject, "sent": bool(send_res.get("sent")), "error": send_res.get("error")})
        print(send_res)
        if args.traj_out:
            try:
                rec = {
                    "mode": "meeting_email",
                    "subject": args.subject,
                    "recipients": attendees,
                    "body_text_length": len(body_text),
                    "steps": steps,
                    "result": send_res,
                }
                with open(args.traj_out, "a", encoding="utf-8") as f:
                    import json as _json
                    f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception:
                pass
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
