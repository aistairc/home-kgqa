#!/usr/bin/env python
# coding: utf-8

"""
Question generation script for KGQA dataset.
Generates questions for different answer types and saves them to JSONL files.
"""

import json
import pickle
import os
import sys
import argparse
import spacy
import en_core_web_sm
from genqa.extract import *
from genqa.config import SCENE, ANSWER_TYPE_OPTIONS, DEFAULT_LOOP, SEEN_COMBINATIONS_FILE
from genqa.question_generator import QuestionGenerator

# Initialize NLP and extractor
nlp = en_core_web_sm.load()
extractor = Extractor(repository="http://localhost:7200/repositories/vhakg-episode-" + SCENE, scene=SCENE)

# Initialize question generator
question_generator = QuestionGenerator(extractor)

def generateQuestions(loop, selected_answer_type, seen_combinations):
    return question_generator.generate_questions(loop, selected_answer_type, seen_combinations)


def main(loop=None, answer_types=None, output_dir='generated_questions'):
    """Main function to generate questions with specified parameters."""
    if loop is None:
        loop = DEFAULT_LOOP
    if answer_types is None:
        answer_types = ANSWER_TYPE_OPTIONS
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load OpenAI API key from config file
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            os.environ["OPENAI_API_KEY"] = config["openai_api_key"]
    except FileNotFoundError:
        print("Error: config.json file not found. Please create a config.json file with your OpenAI API key.")
        sys.exit(1)
    except KeyError:
        print("Error: 'openai_api_key' not found in config.json file.")
        sys.exit(1)

    # Load seen combinations
    seen_combinations = set()
    if os.path.exists(SEEN_COMBINATIONS_FILE):
        with open(SEEN_COMBINATIONS_FILE, 'rb') as f:
            seen_combinations = pickle.load(f)
    else:
        print(f"Seen combinations file not found at {SEEN_COMBINATIONS_FILE}. Starting with empty set.")
    
    # Generate questions for selected answer types
    for selected_answer_type in answer_types:
        print(f"Generating {loop} questions for answer type: {selected_answer_type}")
        dataset, seen_combinations = generateQuestions(loop, selected_answer_type, seen_combinations)
        output_file = f"{output_dir}/question_dataset_{selected_answer_type}_{loop}.jsonl"
        with open(output_file, 'w') as outfile:
            json.dump(dataset, outfile)
        print(f"Saved {len(dataset)} questions to {output_file}")

    # Save seen combinations
    with open(SEEN_COMBINATIONS_FILE, 'wb') as f:
        pickle.dump(seen_combinations, f)
    print("Saved seen combinations for future runs")


# Main Execution
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate questions for KGQA dataset')
    parser.add_argument('--loop', '-l', type=int, default=DEFAULT_LOOP, 
                       help=f'Number of questions to generate (default: {DEFAULT_LOOP})')
    parser.add_argument('--answer-types', '-a', nargs='+', default=ANSWER_TYPE_OPTIONS,
                       choices=ANSWER_TYPE_OPTIONS, help='Answer types to generate questions for')
    parser.add_argument('--output-dir', '-o', default='generated_questions',
                       help='Output directory for generated files')
    
    args = parser.parse_args()
    
    # Call main function with parsed arguments
    main(loop=args.loop, answer_types=args.answer_types, output_dir=args.output_dir)