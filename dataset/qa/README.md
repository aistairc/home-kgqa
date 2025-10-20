# QA Datasets

Pre-generated datasets for evaluating KGQA models.

## Contents
- `*_compositional_*.jsonl` denotes the compositional generalization split: all relations and classes are seen during training, but specific logical-form constructs and operators that appear in the test set are unseen.
- `*_iid_*.jsonl` denotes the i.i.d. generalization split: relations, classes, and logical-form constructs (e.g., SPARQL modifiers, FILTER expressions, operators) are seen during training, but entities and literals differ between train and test.

## Format

Each file uses the JSON Lines (JSONL) format. Each line is a JSON object with at least the following fields:

- `question_text_en`: The question text (English)
- `query`: The SPARQL query used to retrieve the answer(s)
- `results`: The SPARQL execution results
- `paraphrased_question_text_en`: A paraphrased version of the question (English)
- `selected_answer_type`: The answer category (e.g., Space, Time, Object, Aggregation, Activity, Video)
- `selected_answer_type_metadata`: Additional detail for the answer type (e.g., for Aggregation: Count, Min, Max, Avg)
- `selected_answer_type_metadata_value`: The variable/property the answer type refers to (e.g., `pos_z` when Aggregation = Max)
- `query_pattern_Object_type`: Type of object specifier in the pattern (Class, Instance, None)
- `query_pattern_Object_value`: The object value (e.g., Decor, Refrigerator123)
- `query_pattern_Action_type`: Type of action specifier (= None)
- `query_pattern_Action_value`: The action value (e.g., lookAt, putIn)
- `query_pattern_Space_type`: Type of spatial qualifier (e.g., Place, Pos3D, None)
- `query_pattern_Space_value`: The spatial qualifier value (e.g., livingroom, kitchen)
- `query_pattern_Time_type`: Type of temporal qualifier (e.g., Duration, Timestamp, None)
- `query_pattern_Time_value`: The temporal qualifier value (e.g., 17, "2024-06-15T08:30:00")
- `query_pattern_Space_operator`: Comparison operator used for the spatial qualifier (e.g., <, >)
- `query_pattern_Time_operator`: Comparison operator used for the temporal qualifier (e.g., <= <)
- `qualifiers_en`: JSON data for question generation
