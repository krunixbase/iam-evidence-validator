import argparse, json, uuid
from pathlib import Path
from datetime import datetime

def render_report(template_path: Path, output_path: Path, context: dict):
    template = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    output_path.write_text(template, encoding="utf-8")

def load_users(path: Path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()[1:]

def load_roles(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def count_pdfs(path: Path):
    if not path.exists():
        return 0
    return len(list(path.glob("*.pdf")))

def find_orphaned_users(users, roles):
    return [u for u in users if u not in roles]

def privileged_without_review(privileged_users, review_count):
    return privileged_users if review_count == 0 else []

def main():
    parser = argparse.ArgumentParser(description="IAM Evidence Validator")
    parser.add_argument("--input", required=True, help="Evidence folder path")
    parser.add_argument("--output", default="report.html", help="Output HTML report")
    args = parser.parse_args()

    evidence_path = Path(args.input)
    if not evidence_path.exists():
        raise SystemExit(f"Input path does not exist: {evidence_path}")

    controls_path = Path(__file__).with_name("controls.json")
    template_path = Path(__file__).with_name("report_template.html")
    output_path = Path(args.output)

    controls = json.loads(controls_path.read_text(encoding="utf-8"))

    users = load_users(evidence_path / "users.csv")
    roles = load_roles(evidence_path / "roles.json")
    access_reviews = count_pdfs(evidence_path / "access_reviews")
    privileged_users = load_users(evidence_path / "privileged" / "admins.csv")

    orphaned = find_orphaned_users(users, roles)
    privileged_gaps = privileged_without_review(privileged_users, access_reviews)

    context = {
        "report_id": f"IAM-{uuid.uuid4().hex[:8].upper()}",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "validator_version": "1.0.0",
        "client_or_system": "Demo IAM Environment",
        "standard": "IAM / SOC 2 CC6",
        "evidence_scope": "User access, roles, access reviews, privileged accounts",
        "evidence_path": str(evidence_path.resolve()),
        "files_scanned": len(list(evidence_path.rglob("*"))),
        "controls_mapped": len(controls.get("controls", [])),
        "users_total": len(users),
        "roles_total": len(roles),
        "orphaned_accounts": len(orphaned),
        "access_reviews_found": access_reviews,
        "privileged_accounts": len(privileged_users),
        "findings_total": len(orphaned) + len(privileged_gaps),
        "crit_high_count": len(privileged_gaps),
        "evidence_gaps_count": len(orphaned),
        "retest_required": "Yes" if orphaned or privileged_gaps else "No",
    }

    render_report(template_path, output_path, context)
    print(f"Report written to: {output_path.resolve()}")

if __name__ == "__main__":
    main()
