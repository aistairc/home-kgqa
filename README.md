# HOME-KGQA

A benchmark dataset designed to evaluate KGQA (Knowledge Graph Question Answering) models in daily activity environments


## Quick Start

If you want to use the dataset, you can find them in the following directories:

- **QA Datasets**: `dataset/qa/` - Contains train/test datasets for question answering ([details in README](dataset/qa/))
- **Prompt Datasets**: `dataset/prompt/` - Contains prompt datasets for instruction tuning ([details in README](dataset/prompt/))
- **KG Datasets**: `dataset/kg/` - Contains episodic KG datasets, which are the target KGs for KGQA ([details in README](dataset/kg/))


> **Note**: If you only want to use the pre-generated datasets, you do not need to run any of the following sections. The sections below are only for rebuilding or augmenting the datasets.

## Setup

0. **Install uv (if not installed)**:
   - macOS/Linux:
   ```bash
   curl -Ls https://astral.sh/uv/install.sh | sh
   ```
   - Homebrew (macOS):
   ```bash
   brew install uv
   ```

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure OpenAI API key**:
   - Edit `config.json` and replace `your-openai-api-key-here` with your OpenAI API key

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

## License

- **Datasets**: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **Code**: [MIT License](https://opensource.org/licenses/MIT)
