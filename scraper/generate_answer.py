import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from graph_rag_retrieve import graph_reranked_top_products, get_structured_by_name

  # Set this in your environment


def build_prompt(query, top_products):
    context_blocks = []
    structured = json.load(open("data/structured_product_data.json"))

    for i, (score, meta) in enumerate(top_products):
        product_struct = get_structured_by_name(meta["product_name"], structured)
        features = product_struct.get("features_benefits", "").strip()
        ingredients = product_struct.get("ingredients", "").strip()

        # Grab only the first sentence of the feature as a short description
        short_desc = (
            features.split(".")[0].strip() if features else "No description available"
        )

        context_blocks.append(
            f"""
[{i+1}] {meta['product_name']}
URL: {meta['url']}
Brand: {meta['brand']}
Category: {meta['category']}
Features: {short_desc}
Ingredients: {ingredients or 'N/A'}
"""
        )

    context = "\n".join(context_blocks)

    system_prompt = """
You are a friendly expert on Nestlé products. When answering the user's question:

- Start with a concise and helpful summary.
- Then list the top 3 matching products like this:

  1. Product Name – short description.
     [1] View Product →

- Use the [1], [2], etc. references to match the right product.
- End the answer with a friendly section:
  "You might also be interested in:"
  followed by 3 smart follow-up searches.

Be accurate and helpful. Never make up ingredients or benefits.
"""

    user_prompt = f"""
Here are the top 3 matched Nestlé products:

{context}

User question: "{query}"

Answer using the format above.
"""

    return system_prompt.strip(), user_prompt.strip()


def generate_answer(query):
    top_products = graph_reranked_top_products(query, return_data=True)
    system, user = build_prompt(query, top_products)

    print("🧠 Sending to LLM...\n")

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ],
    temperature=0.7,
    max_tokens=600)

    print("✅ Answer:\n")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        query = input("Ask a Nestlé product question: ").strip()
    else:
        query = " ".join(sys.argv[1:])

    generate_answer(query)
