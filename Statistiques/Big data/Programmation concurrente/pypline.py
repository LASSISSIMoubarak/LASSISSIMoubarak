from transformers import pipeline

# Load summarization pipeline with the fine-tuned model
summarizer = pipeline(
    "summarization",
    model="bcool315/bcool-bart-finetuned-dialogue"
)

text = """John: Hey! I've been thinking about getting a PlayStation 5. Do you think it is worth it?
Dan: Idk man. R u sure ur going to have enough free time to play it?
John: Yeah, that's why I'm not sure if I should buy one or not. I've been working so much lately idk if I'm gonna be able to play it as much as I'd like."""

generated_summary = summarizer(text)

print("Original Dialogue:\n")
print(text)
print("\nModel-generated Summary:\n")
print(generated_summary[0]['summary_text'])
