import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_datasets
from identity_resolver import IdentityResolver
from intent_agent import IntentAgent
from audit_engine import AuditEngine
from formatter import sort_and_format_steps

def run_pipeline():
    print("=== BẮT ĐẦU CHẠY PIPELINE AUDIT (ĐÃ TỐI ƯU ĐA LUỒNG) ===")
    
    datasets = load_all_datasets()
    requests_df = datasets["deletion_requests"]
    
    print("-> Khởi tạo Identity Resolver, Intent Agent và Audit Engine...")
    resolver = IdentityResolver(datasets["user_identities"], datasets["user_audit_log"])
    intent_agent = IntentAgent()
    audit_engine = AuditEngine(datasets["system_activity"], datasets["deletion_rules"])
    
    # 1. Phân loại song song tất cả 518 cases bằng Multithreading
    print("-> Đang phân loại ý định (Intent Classification) đa luồng...")
    request_texts = requests_df["request_text"].tolist()
    is_deletion_flags = intent_agent.classify_batch(request_texts)
    
    results = []
    total_cases = len(requests_df)
    
    # 2. Xử lý audit logic
    print("-> Đang kiểm tra dấu vết hệ thống (Audit Engine)...")
    for idx, row in requests_df.iterrows():
        case_id = row.get("case_id")
        email = row.get("email")
        audit_at = row.get("audit_at")
        is_deletion = is_deletion_flags[idx]
        
        if not is_deletion:
            status = "NOT_APPLICABLE"
            steps_json = "[]"
        else:
            identities = resolver.resolve_user_identity(email)
            status, steps = audit_engine.audit_case(identities, audit_at)
            steps_json = sort_and_format_steps(steps)
            
        results.append({
            "case_id": case_id,
            "deletion_status": status,
            "steps_json": steps_json
        })

    # 3. Lưu file output.csv
    output_df = pd.DataFrame(results)
    if "case_id" in output_df.columns:
        output_df = output_df.sort_values(by="case_id")
        
    output_path = "output.csv"
    output_df.to_csv(output_path, index=False)
    print(f"\n=== TẠO THÀNH CÔNG FILE OUTPUT: {output_path} ({len(output_df)} dòng) ===")

    # 4. Cập nhật báo cáo
    eval_dir = os.path.join(os.path.dirname(__file__), "evaluation")
    os.makedirs(eval_dir, exist_ok=True)
    report_content = f"""# Usage Report

- **Total Requests Processed:** {total_cases}
- **Model Used:** `deepseek-chat`
- **Primary Tasks:** Deletion Intent Classification & Evidence Analysis
- **Status Breakdown:**
  - `COMPLETE`: {len(output_df[output_df['deletion_status'] == 'COMPLETE'])}
  - `INCOMPLETE`: {len(output_df[output_df['deletion_status'] == 'INCOMPLETE'])}
  - `NOT_APPLICABLE`: {len(output_df[output_df['deletion_status'] == 'NOT_APPLICABLE'])}
"""
    with open(os.path.join(eval_dir, "usage_report.md"), "w", encoding="utf-8") as f:
        f.write(report_content)
    print("-> Đã cập nhật báo cáo: code/evaluation/usage_report.md")

if __name__ == "__main__":
    run_pipeline()