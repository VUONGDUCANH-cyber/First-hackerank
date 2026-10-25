import pandas as pd

class AuditEngine:
    def __init__(self, system_activity_df: pd.DataFrame, deletion_rules_df: pd.DataFrame):
        self.activity_df = system_activity_df
        self.rules_df = deletion_rules_df

    def audit_case(self, user_identities: dict, audit_at: str) -> tuple[str, list[dict]]:
        steps = []
        user_ids = [str(u) for u in user_identities.get("user_ids", []) if u]
        emails = [str(e).lower() for e in user_identities.get("emails", []) if e]
        phones = [str(p) for p in user_identities.get("phones", []) if p]
        
        # Gom tất cả các từ khóa định danh để quét
        search_terms = user_ids + emails + phones

        if not search_terms:
            return "COMPLETE", [{
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "user_record",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "system_audit_clean"
            }]

        # Hàm kiểm tra xem dòng hoạt động có liên quan đến user hay không
        def matches_user(row):
            # Check cột user_id nếu tồn tại
            if 'user_id' in row and pd.notna(row['user_id']):
                if str(row['user_id']) in user_ids:
                    return True
            
            # Check trong cột details
            details = str(row.get('details', '')).lower()
            if any(term in details for term in search_terms):
                return True

            # Check trong cột resource_id
            res_id = str(row.get('resource_id', '')).lower()
            if any(term in res_id for term in search_terms):
                return True

            return False

        # Lọc các dòng liên quan
        mask = self.activity_df.apply(matches_user, axis=1)
        user_activities = self.activity_df[mask]

        findings = []
        remediations = []
        verifications = []

        audit_dt = pd.to_datetime(audit_at, errors='coerce')

        for _, row in user_activities.iterrows():
            sys_id = str(row.get('system_id', 'unknown'))
            res_id = str(row.get('resource_id', 'unknown'))
            act_type = str(row.get('activity_type', '')).upper()
            status = str(row.get('status', '')).upper()
            act_id = str(row.get('activity_id', ''))
            timestamp = pd.to_datetime(row.get('timestamp'), errors='coerce')

            if pd.notna(timestamp) and pd.notna(audit_dt) and timestamp <= audit_dt:
                # Tiến trình active sync/backup
                if status == 'ACTIVE' or 'SYNC' in act_type or 'BACKUP' in act_type:
                    if 'SYNC' in act_type or status == 'ACTIVE':
                        findings.append({
                            "phase": "FINDING",
                            "system_id": sys_id,
                            "resource_id": res_id,
                            "operation": "REPORT_ACTIVE_DATA_FLOW",
                            "state": "ACTIVE",
                            "evidence_id": act_id
                        })
                        remediations.append({
                            "phase": "REMEDIATION",
                            "system_id": sys_id,
                            "resource_id": res_id,
                            "operation": "DISABLE_DATA_FLOW",
                            "state": "DISABLED",
                            "evidence_id": ""
                        })
                        verifications.append({
                            "phase": "VERIFICATION",
                            "system_id": sys_id,
                            "resource_id": res_id,
                            "operation": "VERIFY_DATA_FLOW_DISABLED",
                            "state": "DISABLED",
                            "evidence_id": ""
                        })
                # Bản ghi chưa xử lý thành công
                elif status in ['FAILED', 'PENDING', 'EXPOSED']:
                    findings.append({
                        "phase": "FINDING",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REPORT_REMAINING_RECORD",
                        "state": "PRESENT",
                        "evidence_id": act_id
                    })
                    remediations.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "DELETE_RECORD",
                        "state": "ABSENT",
                        "evidence_id": ""
                    })
                    verifications.append({
                        "phase": "VERIFICATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": ""
                    })

        if findings:
            status = "INCOMPLETE"
            steps = findings + remediations + verifications
        else:
            status = "COMPLETE"
            verifications.append({
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": user_ids[0] if user_ids else "user_record",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "system_audit_clean"
            })
            steps = verifications

        return status, steps