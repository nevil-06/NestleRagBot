# 🧠 Nestlé Product Search Assistant

An intelligent chatbot and search system built using Nestlé's product and recipe data — with scraping, semantic search, product graph, and OpenAI-powered answers.

---

## 🚀 Quick Start

### 1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/nestle-product-assistant.git
cd nestle-product-assistant
```

### 2. **Install Requirements**

Make sure you have Python 3.8+ installed.

```bash
pip install -r requirements.txt
```

### 3. **Set Your OpenAI Key**

Create a `.env` file in the root folder:

```env
OPENAI_API_KEY=your_openai_key_here
```

Or export it directly:

```bash
export OPENAI_API_KEY=your_openai_key_here
```

### 4. **Run the FastAPI Server**

```bash
uvicorn scraper.app:app --reload --port 8000
```

This will automatically:
- Scrape + index all product data (if not already done)
- Launch an API server

### 5. **Open the App in Your Browser**

Go to:  
👉 [http://localhost:8000/docs](http://localhost:8000/docs)  

Here you can:
- Use the `/answer` endpoint
- Ask product questions like:
  - `"What are some sugar-free Nestlé snacks?"`
  - `"Which Nestlé drinks are good for energy?"`

---

## 🔎 Features

- ✅ Web scraping for Nestlé products and recipes  
- ✅ Semantic vector search (FAISS)  
- ✅ Graph-based product enrichment (NetworkX)  
- ✅ Hybrid reranking with optional CrossEncoder  
- ✅ Natural language answer generation via OpenAI  
- ✅ REST API with FastAPI + Swagger UI  

---

## 🛠️ Project Structure

```
scraper/
├── app.py                   # FastAPI app
├── generate_answer.py       # Builds LLM prompt from top products
├── graph_rag_retrieve.py    # Semantic + graph reranker
├── index_to_vectorstore.py  # Embeds product chunks
├── parse_flat_product_data.py # Converts raw scrape into structured format
├── build_product_graph_nx.py  # Builds product → brand/category/ingredient graph
├── recipe_scraper.py        # Optional recipe scraping
```

---

## 💡 Notes

- This project uses `faiss` for local vector indexing.
- Optionally, you can migrate to Azure Cognitive Search or Vertex AI Matching Engine for enterprise-grade performance (see roadmap).
- If data is already indexed, startup is instant.

---

## 🤖 Example Query

```
POST /answer
{
  "query": "What Nestlé chocolate bars have hazelnuts?"
}
```

---

## 📞 Support

If you get stuck or want to extend the system (e.g. add a Streamlit UI), just open an issue or ping me.