from transformers import GPT2Tokenizer

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
tokenizer.save_pretrained("modelo_kazu_v2")
print("✅ Archivos de vocabulario y merges guardados.")
