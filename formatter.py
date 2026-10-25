import json

# Định nghĩa thứ tự ưu tiên của Phase
PHASE_ORDER = {
    "FINDING": 1,
    "REMEDIATION": 2,
    "VERIFICATION": 3
}

# Định nghĩa thứ tự ưu tiên của Operation
OPERATION_ORDER = {
    # FINDING
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
    
    # REMEDIATION
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
    
    # VERIFICATION
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6
}

def sort_and_format_steps(steps: list[dict]) -> str:
    """
    Sắp xếp các bước (steps) theo quy tắc đề bài và trả về chuỗi JSON string chuẩn.
    Nếu danh sách rỗng (NOT_APPLICABLE), trả về '[]'.
    """
    if not steps:
        return "[]"

    # Định nghĩa hàm lấy key sắp xếp cho từng step
    def sort_key(step):
        phase_priority = PHASE_ORDER.get(step.get("phase", ""), 99)
        op_priority = OPERATION_ORDER.get(step.get("operation", ""), 99)
        sys_id = str(step.get("system_id", "")).lower()
        res_id = str(step.get("resource_id", "")).lower()
        return (phase_priority, op_priority, sys_id, res_id)

    # 1. Sắp xếp danh sách steps
    sorted_steps = sorted(steps, key=sort_key)

    # 2. Gán lại step_no từ 1 đến N
    formatted_steps = []
    for idx, step in enumerate(sorted_steps, start=1):
        formatted_step = {
            "step_no": idx,
            "phase": step.get("phase", ""),
            "system_id": step.get("system_id", ""),
            "resource_id": step.get("resource_id", ""),
            "operation": step.get("operation", ""),
            "state": step.get("state", ""),
            "evidence_id": step.get("evidence_id", "")
        }
        formatted_steps.append(formatted_step)

    # Trả về chuỗi JSON phẳng không có khoảng trắng thừa (compact json)
    return json.dumps(formatted_steps, ensure_ascii=False)

if __name__ == "__main__":
    test_steps = [
        {
            "phase": "VERIFICATION",
            "system_id": "b_system",
            "resource_id": "res_1",
            "operation": "VERIFY_RECORD_ABSENT",
            "state": "ABSENT",
            "evidence_id": ""
        },
        {
            "phase": "FINDING",
            "system_id": "a_system",
            "resource_id": "res_2",
            "operation": "REPORT_REMAINING_RECORD",
            "state": "PRESENT",
            "evidence_id": "ev_01"
        }
    ]

    res_json = sort_and_format_steps(test_steps)
    print("--- KIỂM TRA FORMATTER & SORTING ---")
    print(res_json)