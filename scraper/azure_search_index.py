from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile
)
import os
from dotenv import load_dotenv

load_dotenv()

# Azure Search credentials
endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
key = os.getenv("AZURE_SEARCH_KEY")
index_name = "nestle-index"

client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))

index = SearchIndex(
    name=index_name,
    fields=[
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="chunk_type", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="product_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="brand", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="category", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="url", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="description", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="features_benefits", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="weight", type=SearchFieldDataType.String),
        SearchField(name="ingredients", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="nutrition", type=SearchFieldDataType.String),
        SearchField(name="recipe_title", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="prep_time", type=SearchFieldDataType.String),
        SearchField(name="cook_time", type=SearchFieldDataType.String),
        SearchField(name="servings", type=SearchFieldDataType.String),
        SearchField(name="skill_level", type=SearchFieldDataType.String),
        SearchField(name="title", type=SearchFieldDataType.String),
        SearchField(name="published", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=1536,
            vector_search_profile_name="my-vector-profile"
        )
    ],
    vector_search=VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="my-vector-profile",
                algorithm_configuration_name="my-hnsw"
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(
                name="my-hnsw",
                kind="hnsw"
            )
        ]
    )
)

client.create_index(index)
print("✅ Index 'nestle-index' created successfully.")
