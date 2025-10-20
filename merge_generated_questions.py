#!/usr/bin/env python
# coding: utf-8

import glob
import json
import argparse
import os

def main(loop, file_type="test"):
    """Merge all question files for specified loop and file type."""
    # すべてのJSONファイルを取得
    pattern = f"./generated_questions/question_dataset_{loop}_paraphrased_{file_type}.jsonl"
    json_files = glob.glob(pattern)
    
    if not json_files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    merged_data = []
    
    # 各JSONファイルを読み込んでマージ
    for file in json_files:
        print(f"Loading {file}")
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            merged_data.extend(data)
    
    # マージしたデータを保存
    output_file = f"./generated_questions/merged_question_dataset_{loop}_paraphrased_{file_type}.jsonl"
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(merged_data, outfile, ensure_ascii=False, indent=4)
    
    print(f"Merged {len(json_files)} files into '{output_file}'")
    print(f"Total questions: {len(merged_data)}")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Merge generated question files')
    parser.add_argument('--loop', '-l', type=int, required=True,
                       help='Number of questions to process (must match the loop value used in generate_questions.py)')
    parser.add_argument('--type', '-t', choices=['train', 'test'], default='test',
                       help='Type of files to merge (train or test, default: test)')
    
    args = parser.parse_args()
    
    # Call main function with parsed arguments
    main(args.loop, args.type)