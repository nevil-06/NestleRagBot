from openai import OpenAI

import os, json
from graph_rag_retrieve import graph_reranked_top_products
from dotenv import load_dotenv
from graph_rag_retrieve import get_structured_by_name  # make sure this is imported



load_dotenv()

# Make sure to set this in your environment
os.environ["TOKENIZERS_PARALLELISM"] = "false"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def build_prompt(query, top_products):
    structured = json.load(open("data/structured_product_data.json"))
    context_blocks = []

    for i, (score, meta) in enumerate(top_products):
        # ✅ Pull full structured data
        product_struct = get_structured_by_name(meta["product_name"], structured)
        features = product_struct.get("features_benefits", "").strip()
        ingredients = product_struct.get("ingredients", "").strip()

        # ✅ Build each product block
        context_blocks.append(f"""
    Product #{i+1}:
    Name: {meta['product_name']}
    Brand: {meta['brand']}
    Category: {meta['category']}
    Features: {features or 'N/A'}
    Ingredients: {ingredients or 'N/A'}
    URL: {meta['url']}
    """)


    context = "\n".join(context_blocks)

    system_prompt = """
You are an expert and helpful assistant on Nestlé products. Be concise, friendly, and informative.
If the user's question is about ingredients, health, flavors, or comparisons, answer using only the products provided.

At the end of your answer, suggest 3 interesting follow-up queries based on what the user might want to know next.
"""

    user_prompt = f"""
Here are the top related Nestlé products based on the user query:

{context}

User question: "{query}"

Answer the question using the information above. Then suggest 3 search prompts.
"""

    return system_prompt.strip(), user_prompt.strip()


def generate_answer(query):
    # Get top 3 product tuples (score, metadata)
    top_products = graph_reranked_top_products(query, return_data=True)

    system, user = build_prompt(query, top_products)

    print("🧠 Sending to LLM...\n")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        max_tokens=600,
    )

    print("✅ Answer:\n")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        query = input("Ask a Nestlé product question: ").strip()
    else:
        query = " ".join(sys.argv[1:])

    generate_answer(query)
