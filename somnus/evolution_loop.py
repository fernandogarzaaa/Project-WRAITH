import os
import json
import glob

RAW_DIR = r"D:\Project Wraith\data\raw"
PROCESSED_DIR = r"D:\Project Wraith\data\processed"
DATASET_PATH = os.path.join(PROCESSED_DIR, "dataset.jsonl")

def format_to_alpaca(raw_text):
    """
    Very basic conversion from raw text to an Alpaca-style instruction format.
    You may want to adjust the prompt generation based on your actual data structure.
    """
    # Assuming the raw text contains some knowledge we want the model to learn.
    return {
        "instruction": "Analyze and summarize the following information.",
        "input": "",
        "output": raw_text.strip()
    }

def process_raw_data():
    """
    Reads text/json files from RAW_DIR and converts them to Alpaca-style JSONL.
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # We will look for .txt and .json files in the raw directory
    file_patterns = ["*.txt", "*.json"]
    files_to_process = []
    
    for pattern in file_patterns:
        files_to_process.extend(glob.glob(os.path.join(RAW_DIR, pattern)))
        
    print(f"Found {len(files_to_process)} files to process in {RAW_DIR}")
    
    dataset_entries = []
    
    for file_path in files_to_process:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if file_path.endswith('.json'):
                # Try to parse and extract relevant text, fallback to string if simple structure
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        # Attempt to extract text fields or just stringify
                        content = json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    pass
            
            if content.strip():
                dataset_entries.append(format_to_alpaca(content))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    # Write to JSONL
    with open(DATASET_PATH, 'w', encoding='utf-8') as out_f:
        for entry in dataset_entries:
            out_f.write(json.dumps(entry) + '\n')
            
    print(f"Saved {len(dataset_entries)} entries to {DATASET_PATH}")
    return DATASET_PATH

def trigger_unsloth_lora_finetune(dataset_path):
    """
    Stub function to trigger a background LoRA fine-tune using unsloth.
    """
    print(f"Preparing to fine-tune using dataset: {dataset_path}")
    print("Initializing unsloth...")
    
    # --- UNSLOTH STUB ---
    # In a real scenario, you would import unsloth here, but we keep it as a stub
    # so the script can run without failing if unsloth isn't installed yet.
    
    stub_code = """
    from unsloth import FastLanguageModel
    import torch
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
    
    max_seq_length = 2048
    dtype = None # None for auto detection
    load_in_4bit = True # Use 4bit quantization to reduce memory usage

    # 1. Load Model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/Qwen2.5-7B-Instruct",
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )
    
    # 2. Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        use_rslora = False,
        loftq_config = None,
    )
    
    # 3. Load and format dataset
    dataset = load_dataset("json", data_files={"train": dataset_path}, split="train")
    
    # Formatting function for Alpaca
    alpaca_prompt = \"\"\"Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

    ### Instruction:
    {}

    ### Input:
    {}

    ### Response:
    {}
    \"\"\"
    
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(instruction, input, output) + tokenizer.eos_token
            texts.append(text)
        return { "text" : texts, }
    
    dataset = dataset.map(formatting_prompts_func, batched = True,)
    
    # 4. Train
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False, # Can make training 5x faster for short sequences
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_steps = 5,
            max_steps = 60,
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )
    
    trainer_stats = trainer.train()
    
    # 5. Save Model
    model.save_pretrained("lora_model")
    tokenizer.save_pretrained("lora_model")
    print("Fine-tuning complete. LoRA adapters saved to 'lora_model'")
    """
    
    print("Unsloth LoRA fine-tuning logic is implemented in the stub.")
    print("To execute the fine-tune in the background, you could save the stub to a script and run it via subprocess.")
    print("For now, this is just a simulation.")

def main():
    print("Starting Evolution Loop...")
    dataset_path = process_raw_data()
    trigger_unsloth_lora_finetune(dataset_path)
    print("Evolution Loop cycle complete.")

if __name__ == "__main__":
    main()
