from fastapi import UploadFile, File
from mcp.server.fastmcp import FastMCP
from elasticsearch import Elasticsearch, exceptions
import config

es_mcp = FastMCP("ES Tools")

es = Elasticsearch([config.ES_HOST], basic_auth=(config.ES_USERNAME, config.ES_PASSWORD))

mapping = {
      "properties": {
        "filename": { "type": "text" },
        "file_content": { "type": "text" },
      }
}

@es_mcp.tool( name = "create_index" )
def create_index(index_name: str):
    """
    This tool, create_index, is designed to create a new index within Elasticsearch.

    Parameters:
        index_name (string, required): The name you want to give to the new index.

    Functionality:
        The tool first checks if an index with the provided index_name already exists.
        If it does exist, the tool will return a message indicating that the index already exists and will not attempt to create it.
        If it does not exist, the tool will proceed to create a new index with the specified name. Optionally, a mapping (not explicitly shown in the provided snippet but referenced) can be applied during creation to define the structure and data types of documents within the index.

    Returns:
        The tool returns a dictionary with the following keys:
        success (boolean): True if the index was created successfully, False otherwise.
        message (string, optional): A success message if the index was created.
        error (string, optional): An error message if the index creation failed or if the index already existed.    
    """
    if es.indices.exists(index=index_name):
        return {"success": False, "error": f"Index '{index_name}' already exists"}

    try:
        es.indices.create(index=index_name, body={"mappings": mapping} if mapping else None)
        return {"success": True, "message": f"Index '{index_name}' created"}
    except exceptions.ElasticsearchException as e:
        return {"success": False, "error": str(e)}

@es_mcp.tool( name = "add_document" )
def add_document(index_name: str, filename: str, file_content: str):
    """
    This tool, add_document, is designed to add a new document to a specified index within Elasticsearch.

    Parameters:
        index_name (string, required): The name of the Elasticsearch index where the document will be added.
        filename (string, required): The name of the file associated with the content being indexed. This will be stored as a field within the document.
        file_content (string, required): The actual content of the file that needs to be indexed. This will be stored as a field within the document.
        
    Functionality:
        The add_document tool constructs a document with filename and file_content fields. It then attempts to index this document into the specified index_name.
        doc_id value taken from a filename unique ID for the document.
        If doc_id exist then it will return doc_id already indexed.

    Returns:
    The tool returns a dictionary with the following keys:
        success (boolean): True if the document was successfully indexed, False otherwise.
        message (string, optional): A success message if the document was indexed.
        error (string, optional): An error message if the document indexing failed.    
    """
    return_data = {"success": True, "message": "Document indexed"}
    try:
        doc_id = filename
        if es.exists(index=index_name, id=doc_id):
            return_data = {"success": False, "message": "Filename : "+filename+" already exist"}
        else:
            document = {"filename": filename, "file_content": file_content}
            es.index(index=index_name, id=doc_id, document=document)
            return_data = {"success": True, "message": "Document indexed"}
    except Exception as e:
        return_data = {"success": False, "message": str(e)}
    
    return return_data

@es_mcp.tool( name = "search_by_keyword" )
def search_by_keyword(index: str, keyword: str):
    """
    This tool, search_by_keyword, is designed to search a specified Elasticsearch index for documents containing a particular keyword within their file_content field.

    Parameters:
        index (string, required): The name of the Elasticsearch index to search within.
        keyword (string, required): The keyword or phrase to search for within the file_content field of the documents.

    Functionality:
    The search_by_keyword tool constructs a match query targeting the file_content field. This query is then executed against the specified Elasticsearch index. The tool retrieves all documents that match the provided keyword in their file_content.

    Returns
    The tool returns a list of dictionaries. Each dictionary in the list represents a document that matched the search query, containing the original source fields of the document (e.g., filename, file_content).
    """
    query = {
        "query": {
            "match": {
                "file_content": keyword
            }
        }
    }
    results = es.search(index=index, body=query)
    return [hit["_source"] for hit in results["hits"]["hits"]]

@es_mcp.tool( name = "search_content_by_filename" )
def get_content_by_filename(index: str, filename: str) -> dict:
    """
    This tool, search_content_by_filename, is designed to retrieve the content of a document from a specified Elasticsearch index by its filename.

    Parameters:
        index (string, required): The name of the Elasticsearch index to search within.
        filename (string, required): The exact filename of the document to retrieve.

    Functionality:
        The search_content_by_filename tool constructs a query that attempts to find documents where the filename field matches the provided filename. 
        It uses a bool query with should clauses to search both for an exact term match on filename.keyword (for precise matching of the whole filename) and a more general match on the filename field (to handle potential tokenization or slight variations).
        The tool then executes this query, limiting the results to the top 1 hit, as it expects to find a unique document for a given filename.

    Returns:
        The tool returns a dictionary containing the filename and file_content of the found document. 
        If no document is found with the specified filename, it returns a dictionary with an "error" key.    
    """
    query = {
        "query": {
            "bool": {
                "should": [
                    { "term": { "filename.keyword": filename } },
                    { "match": { "filename": filename } }
                ]
            }
        }
    }

    results = es.search(index = index, body = query, size = 1)
    hits = results["hits"]["hits"]

    if not hits:
        return {"error": f"No document found with filename: {filename}"}

    return {
        "filename": hits[0]["_source"]["filename"],
        "file_content": hits[0]["_source"]["file_content"]
    }

@es_mcp.tool(name="list_doc_ids")
def list_doc_ids(index_name: str) -> dict:
    """
    Lists all document IDs (doc_id) in the specified Elasticsearch index.

    Parameters:
        index_name (string): The name of the Elasticsearch index.

    Returns:
        A dictionary containing the list of document IDs or an error message.
    """
    return_data = {"success": True}
    try:
        results = es.search(index=index_name, query={"match_all": {}})
        doc_ids = [hit["_id"] for hit in results["hits"]["hits"]]
        return_data["doc_ids"] = doc_ids
    except Exception as e:
        return_data = {"success": False, "message" : str(e)}

    return return_data

@es_mcp.tool(name="delete_document")
def delete_document(index_name: str, doc_id: str):
    """
    Deletes a document from the specified Elasticsearch index using the doc_id.

    Parameters:
        index_name (string): The name of the index to delete the document from.
        doc_id (string): The unique ID of the document to be deleted.

    Returns:
        A dictionary indicating success or failure.
    """
    try:
        if not es.exists(index=index_name, id=doc_id):
            return {"success": False, "message": f"No document found with doc_id: {doc_id}"}
        else:
            es.delete(index=index_name, id=doc_id)
            return {"success": True, "message": f"Document with doc_id '{doc_id}' has been deleted from index '{index_name}'."}
    except Exception as e:
        return {"success": False, "message": str(e)}


print("Tools ElasticSearch activated")
