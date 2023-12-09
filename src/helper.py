import argparse
import os

from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer, CrossEncoder, util

from text_generation import Client
from transformers import pipeline


PREPROMPT = "Below are a series of dialogues between various people and an AI assistant. The AI tries to be helpful, polite, honest, sophisticated, emotionally aware, and humble-but-knowledgeable. The assistant is happy to help with almost anything, and will do its best to understand exactly what is needed. It also tries to avoid giving false or misleading information, and it caveats when it isn't entirely sure about the right answer. That said, the assistant is practical and really does its best, and doesn't let caution get too much in the way of being useful.\n"
PROMPT = """"Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to
make up an answer. Don't make up new terms which are not available in the context.
{context}"""

END_40B = "\n<|prompter|>{query}<|endoftext|><|assistant|>"

PARAMETERS = {
    "temperature": 0.9,
    "top_p": 0.95,
    "repetition_penalty": 1.2,
    "top_k": 50,
    "truncate": 1000,
    "max_new_tokens": 1024,
    "seed": 42,
    "stop_sequences": ["<|endoftext|>", "</s>"],
}

pipe = pipeline("text-generation", model="OpenAssistant/falcon-7b-sft-top1-696", trust_remote_code=True)


def embed(fname, window_size, step_size):
    text = extract_text(fname)
    text = " ".join(text.split())
    text_tokens = text.split()

    sentences = []
    for i in range(0, len(text_tokens), step_size):
        window = text_tokens[i : i + window_size]
        sentences.append(window)
        if len(window) < window_size:
            break

    paragraphs = [" ".join(s) for s in sentences]
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    model.max_seq_length = 512
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    embeddings = model.encode(
        paragraphs,
        show_progress_bar=True,
        convert_to_tensor=True,
    )
    return model, cross_encoder, embeddings, paragraphs


def search(query, model, cross_encoder, embeddings, paragraphs, top_k):
    query_embeddings = model.encode(query, convert_to_tensor=True)
    query_embeddings = query_embeddings.cuda()
    hits = util.semantic_search(
        query_embeddings,
        embeddings,
        top_k=top_k,
    )[0]

    cross_input = [[query, paragraphs[hit["corpus_id"]]] for hit in hits]
    cross_scores = cross_encoder.predict(cross_input)

    for idx in range(len(cross_scores)):
        hits[idx]["cross_score"] = cross_scores[idx]

    results = []
    hits = sorted(hits, key=lambda x: x["cross_score"], reverse=True)
    for hit in hits[:5]:
        results.append(paragraphs[hit["corpus_id"]].replace("\n", " "))
    return results


model, cross_encoder, embeddings, paragraphs = embed(os.path.join("data", "Science - Wikipedia.pdf"), window_size=128, step_size=100)

def chatbot(query):
    top_k=32
    results = search(
        query,
        model,
        cross_encoder,
        embeddings,
        paragraphs,
        top_k=top_k,
    )


    query_40b = PREPROMPT + PROMPT.format(context="\n".join(results))
    query_40b += END_40B.format(query=query)

    sequences = pipe(query_40b,**PARAMETERS)

    return sequences[0]