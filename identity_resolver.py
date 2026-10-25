import pandas as pd

class IdentityResolver:
    def __init__(self, user_identities_df: pd.DataFrame, user_audit_log_df: pd.DataFrame):
        self.identities = user_identities_df
        self.audit_log = user_audit_log_df

    def resolve_user_identity(self, request_email: str) -> dict:
        """
        Tìm tất cả các định danh liên quan đến email từ yêu cầu xóa.
        Trả về dict chứa các tập hợp: emails, user_ids, phones, email_hashes.
        """
        related_emails = set()
        related_user_ids = set()
        related_phones = set()
        related_hashes = set()

        if pd.notna(request_email) and str(request_email).strip():
            email_clean = str(request_email).strip().lower()
            related_emails.add(email_clean)

        # 1. Tìm trong bảng user_identities theo email
        matched_identities = self.identities[
            self.identities['email'].astype(str).str.lower().isin(related_emails)
        ]

        for _, row in matched_identities.iterrows():
            if pd.notna(row.get('user_id')):
                related_user_ids.add(str(row['user_id']))
            if pd.notna(row.get('phone')):
                related_phones.add(str(row['phone']))
            if pd.notna(row.get('email_hash')):
                related_hashes.add(str(row['email_hash']))
            if pd.notna(row.get('email')):
                related_emails.add(str(row['email']).lower())

        # 2. Mở rộng truy vết theo user_id nếu đã tìm thấy user_id
        if related_user_ids:
            more_identities = self.identities[
                self.identities['user_id'].astype(str).isin(related_user_ids)
            ]
            for _, row in more_identities.iterrows():
                if pd.notna(row.get('email')):
                    related_emails.add(str(row['email']).lower())
                if pd.notna(row.get('phone')):
                    related_phones.add(str(row['phone']))
                if pd.notna(row.get('email_hash')):
                    related_hashes.add(str(row['email_hash']))

        # 3. Quét bảng user_audit_log để tìm lịch sử đổi email/phone/user_id
        if related_emails or related_user_ids:
            mask = (
                self.audit_log['user_id'].astype(str).isin(related_user_ids) |
                self.audit_log['old_value'].astype(str).str.lower().isin(related_emails) |
                self.audit_log['new_value'].astype(str).str.lower().isin(related_emails)
            )
            logs = self.audit_log[mask]
            for _, row in logs.iterrows():
                if pd.notna(row.get('user_id')):
                    related_user_ids.add(str(row['user_id']))
                for col in ['old_value', 'new_value']:
                    val = str(row.get(col, '')).strip()
                    if '@' in val:
                        related_emails.add(val.lower())

        return {
            "emails": list(related_emails),
            "user_ids": list(related_user_ids),
            "phones": list(related_phones),
            "email_hashes": list(related_hashes)
        }

if __name__ == "__main__":
    from data_loader import load_all_datasets
    
    datasets = load_all_datasets()
    resolver = IdentityResolver(datasets["user_identities"], datasets["user_audit_log"])
    
    # Test thử với dòng đầu tiên trong deletion_requests.csv
    first_email = datasets["deletion_requests"].iloc[0]["email"]
    res = resolver.resolve_user_identity(first_email)
    
    print(f"--- TEST RESOLVE CHO EMAIL: {first_email} ---")
    print(res)