# HOME-KGQA

A benchmark dataset designed to evaluate KGQA (Knowledge Graph Question Answering) models in daily activity environments

## Quick Start

If you want to use the system immediately with pre-generated datasets, you can find them in the following directories:

- **QA Datasets**: `dataset/qa/` - Contains train/test datasets for question answering
- **Prompt Datasets**: `dataset/prompt/` - Contains prompt datasets for instruction tuning

These datasets are ready to use without additional setup.

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure OpenAI API key**:
   - Edit `config.json` and replace `your-openai-api-key-here` with your actual OpenAI API key

   The configuration file should look like this:
   ```json
   {
     "openai_api_key": "your-openai-api-key-here"
   }
   ```

## Usage

### Generate Questions
```bash
# Generate 10 questions for all answer types
python generate_questions.py --loop 10

# Generate 5 questions for specific answer types
python generate_questions.py --loop 5 --answer-types Space Time Object

# Specify custom output directory
python generate_questions.py --loop 10 --output-dir my_questions
```

### Paraphrase Questions
```bash
# Paraphrase questions generated with loop=10
python paraphrase_questions.py --loop 10
```

### Split Dataset
```bash
# Split all paraphrased questions into train and test sets
python split_dataset.py --loop 10
```

### Merge Questions
```bash
# Merge all test files for loop=10
python merge_generated_questions.py --loop 10 --type test

# Merge all train files for loop=10
python merge_generated_questions.py --loop 10 --type train
```

## Advanced Usage

### Generate Episodic Knowledge Graph

**Note**: This step requires downloading the VHAKG dataset first and is only needed for advanced users.

1. **Download and setup VHAKG dataset**:
   - Download `vhakg_event.tar.gz` and `vhakg_video_base64.tar.gz` from [VHAKG dataset](https://zenodo.org/records/11438499)
   - Place the downloaded files in the `dataset/` directory
   - Extract the archives:
   ```bash
   cd dataset/
   tar -xzf vhakg_event.tar.gz
   tar -xzf vhakg_video_base64.tar.gz
   ```

2. **Generate episodic knowledge graph**:
   ```bash
   # Generate episodic knowledge graph from VHAKG dataset
   python generate_episodic_kg.py
   ```

## File Structure

```
/Users/s-egami/dev/home-kgqa/
├── generate_episodic_kg.py   # Generate episodic knowledge graph from VHAKG dataset
├── generate_questions.py     # Main question generation script
├── paraphrase_questions.py   # Question paraphrasing script
├── split_dataset.py          # Dataset splitting script
├── merge_generated_questions.py # Question merging script
├── config.json               # Configuration file (edit with your API key)
├── dataset/                  # Dataset directory
│   ├── qa/                   # Pre-generated QA datasets (ready to use)
│   │   ├── train_compositional_350.jsonl
│   │   ├── train_iid_350.jsonl
│   │   ├── test_compositional_700.jsonl
│   │   └── test_iid_700.jsonl
│   ├── prompt/               # Pre-generated prompt datasets (ready to use)
│   │   ├── HOE-KGQA_prompt_dataset_paraphrased_compositional.jsonl
│   │   ├── HOE-KGQA_prompt_dataset_paraphrased_iid.jsonl
│   │   ├── HOE-KGQA_prompt_dataset_raw_compositional.jsonl
│   │   └── HOE-KGQA_prompt_dataset_raw_iid.jsonl
│   ├── kg/                   # Knowledge graph files
│   │   └── vh2kg_schema_v2.0.0.ttl
│   ├── vhakg_event.tar.gz    # Event-centric knowledge graphs (download from Zenodo)
│   └── vhakg_video_base64.tar.gz # Video-embedded knowledge graphs (download from Zenodo)
├── genqa/                    # Question generation package
│   ├── __init__.py
│   ├── config.py
│   ├── extract.py
│   ├── query_patterns.py
│   └── question_generator.py
└── generated_questions/      # Output directory for generated files
```
