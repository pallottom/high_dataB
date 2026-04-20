import pandas as pd
from collections import defaultdict

def analyze_csv_files(file_paths):
    # Track occurrence of each column across files
    column_count = defaultdict(int)
    file_results = {}
    total_files = len(file_paths)

    for file in file_paths:
        df = pd.read_csv(file)
        current_file_data = {}

        for col in df.columns:
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) < 10:
                unique_list = list(unique_vals)
            else:
                unique_list = None  # Too many unique values

            column_count[col] += 1
            current_file_data[col] = unique_list

        file_results[file] = current_file_data

    # Columns present in all files
    common_columns = {col: None for col, count in column_count.items() if count == total_files}

    # File-specific or partially shared columns (exclude common ones)
    refined_per_file = {}
    for file, cols in file_results.items():
        refined_per_file[file] = {
            col: vals for col, vals in cols.items() if col not in common_columns
        }

    result = {
        "common_columns": common_columns  # Only columns present in ALL files
    }
    result.update(refined_per_file)
    return result


def save_report_to_text(result_dict, output_path="column_report.txt"):
    with open(output_path, "w", encoding="utf-8") as file:
        for section, data in result_dict.items():
            file.write(f"{section}:\n")
            for col, vals in data.items():
                file.write(f"  {col}  →  {vals}\n")
            file.write("\n")
    print(f"✅ Report saved to {output_path}")



# 🔍 Example usage
files = ["../test_DB/data/GVS_20250822_extendedfeatures.csv",
        "../test_DB/data/IMXPR03S14R02R05_wi_htrf_asc_20251003_JB(in).csv", 
        "../test_DB/data/IMXPR04_postATP_20220224_extendedfeatures (copy).csv",
        "../test_DB/data/IMXPR04_postATP_ready4FeatureVector_JB_20220224 (copy).csv",
        "../test_DB/data/IMXPR05S07R04R05_wi_htrf_icc_20250917_JB.csv"] 

        
         # Replace with your actual paths
result = analyze_csv_files(files)
save_report_to_text(result, "columns_summary_report.txt")