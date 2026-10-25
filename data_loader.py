import os
import pandas as pd
from dotenv import load_dotenv

# Nạp biến môi trường từ file .env
load_dotenv()

DATASET_DIR = "dataset"
if not os.path.exists(DATASET_DIR):
    DATASET_DIR = os.path.join("..", "dataset")
def load_all_datasets():
    """Đọc toàn bộ các file CSV trong thư mục dataset/."""
    datasets = {
        "deletion_requests": pd.read_csv(os.path.join(DATASET_DIR, "deletion_requests.csv")),
        "user_identities": pd.read_csv(os.path.join(DATASET_DIR, "user_identities.csv")),
        "user_audit_log": pd.read_csv(os.path.join(DATASET_DIR, "user_audit_log.csv")),
        "system_activity": pd.read_csv(os.path.join(DATASET_DIR, "system_activity.csv")),
        "deletion_rules": pd.read_csv(os.path.join(DATASET_DIR, "deletion_rules.csv")),
    }
    
    # Kiểm tra nếu file evidence_files.csv tồn tại
    evidence_meta_path = os.path.join(DATASET_DIR, "evidence_files.csv")
    if os.path.exists(evidence_meta_path):
        datasets["evidence_files"] = pd.read_csv(evidence_meta_path)
        
    return datasets

if __name__ == "__main__":
    data = load_all_datasets()
    print("--- KIỂM TRA ĐỌC DỮ LIỆU ---")
    for name, df in data.items():
        print(f"- {name}: {len(df)} dòng")