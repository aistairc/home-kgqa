import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Process a JSONL file to create a prompt dataset.")
    parser.add_argument("--input_file", help="Path to the input JSONL file")
    parser.add_argument("--output_file", help="Path to the output JSONL file")
    parser.add_argument("--language", choices=["en", "ja"], default="en", 
                        help="Language for the prompt template: 'en' for English, 'ja' for Japanese (default: en)")
    parser.add_argument("--qlevel", type=int, choices=[0, 1, 2], default=0, 
                        help="Question level: 0 for 'question_text', 1 for 'modified_question_text1', 2 for 'modified_question_text2' (default: 0)")
    args = parser.parse_args()

    input_file = args.input_file
    qlevel = args.qlevel
    language = args.language
    output_file = args.output_file
    

    # プロンプトテンプレートの定義
    prompt_template = None
    system_message = ""
    if language == "en":
        system_message = "You are a SPARQL query generator. Generate a SPARQL query based on the given question. Do not output anything other than the SPARQL query."
        prompt_template = ("Question:\n{question}\n\nSPARQL:\n")
    elif language == "ja":
        system_message = "あなたはSPARQLクエリジェネレーターです。与えられた質問文をもとにSPARQLクエリを生成してください。SPARQLクエリ以外を出力しないでください。"
        prompt_template = ("質問文:\n{question}\n\nSPARQL:\n")

    # 入力jsonlファイルから各行のJSONオブジェクトをリストとしてロードする
    with open(input_file, 'r') as f:
        input_dataset = json.load(f)
    
    processed_entries = []
    for data in input_dataset:
        # qlevelに応じて適切な質問テキストを選択
        if qlevel == 0:
            question = data.get(f"question_text_{language}", "")
        elif qlevel == 1:
            question = data.get(f"paraphrased_question_text_{language}", "")
        # elif qlevel == 2:
        #     question = data.get(f"modified_question_text2_{language}", "")
        
        sparql = data.get("query", "")
        
        # プロンプトテンプレートにquestionを埋め込み、プロンプトを作成
        prompt = prompt_template.format(question=question)
        
        # 指定の形式で最終的なJSONオブジェクトを作成
        output_data = {
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role": "assistant",
                    "content": sparql
                }
            ]
        }
        
        processed_entries.append(output_data)
    
    # 全エントリのリストをjsonl形式で一括出力
    with open(output_file, 'w', encoding='utf-8') as outfile:
        jsonl_output = "\n".join(json.dumps(item, ensure_ascii=False) for item in processed_entries)
        outfile.write(jsonl_output + "\n")

if __name__ == '__main__':
    main()