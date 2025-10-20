#!/usr/bin/env python
# coding: utf-8

import json
import argparse
from sklearn.model_selection import train_test_split

def main(loop):
    """Split all question categories into train and test sets."""
    question_categories = ["Object", "Action", "Space", "Time", "Activity", "Video", "Aggregation"]
    
    all_questions = []
    
    # Load all categories
    for category in question_categories:
        dataset_file_name = f"generated_questions/question_dataset_{category}_{loop}_paraphrased"
        try:
            with open(dataset_file_name + ".jsonl", 'r') as f:
                category_questions = json.load(f)
                print(f"Loaded {len(category_questions)} questions from {category}")
                all_questions.extend(category_questions)
        except FileNotFoundError:
            print(f"Warning: {dataset_file_name}.jsonl not found, skipping {category}")
    
    print(f"Total questions loaded: {len(all_questions)}")
    
    # Clean up queries
    for item in all_questions:
        item["query"] = "\n".join([line.strip() for line in item["query"].splitlines() if line.strip()])
    
    # Split the dataset into train and test sets
    train_set, test_set = train_test_split(all_questions, test_size=0.666, random_state=42)
    
    print(f"Train set size: {len(train_set)}")
    print(f"Test set size: {len(test_set)}")
    
    # Save combined dataset
    output_file_name = f"generated_questions/question_dataset_{loop}_paraphrased"
    with open(output_file_name + "_train.jsonl", 'w') as f:
        json.dump(train_set, f, ensure_ascii=False)
    
    with open(output_file_name + "_test.jsonl", 'w') as f:
        json.dump(test_set, f, ensure_ascii=False)
    
    print(f"Saved train set to {output_file_name}_train.jsonl")
    print(f"Saved test set to {output_file_name}_test.jsonl")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Split question dataset into train and test sets')
    parser.add_argument('--loop', '-l', type=int, required=True,
                       help='Number of questions to process (must match the loop value used in generate_questions.py)')
    
    args = parser.parse_args()
    
    # Call main function with parsed arguments
    main(args.loop)

