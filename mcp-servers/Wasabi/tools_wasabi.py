from fastapi import UploadFile, File, Form
from mcp.server.fastmcp import FastMCP, Context
import boto3
import config
import wasabi_helper
import os
import base64

wasabi_mcp = FastMCP("Wasabi Tools")

# Create Wasabi client
s3 = boto3.client(
    's3',
    endpoint_url = config.WASABI_ENDPOINT_URL,
    aws_access_key_id = config.WASABI_ACCESS_KEY,
    aws_secret_access_key = config.WASABI_SECRET_KEY
)


@wasabi_mcp.tool(name = "upload_file")
def upload_file(
    filename: str,
    file_content: str,
    bucket_name: str
) -> str:
    """
    Uploads a given file to a specified Wasabi bucket.

    This function creates a temporary directory named "temp" if it doesn't already exist.
    It then writes the provided file_content to a file with the given filename inside
    this temporary directory. Finally, it uploads this local file to the specified
    Wasabi bucket.

    Args:
        filename (str): The name of the file to be uploaded (e.g., "my_document.txt").
        file_content (str): The content of the file as a string.
        bucket_name (str): The name of the Wasabi bucket where the file will be uploaded.

    Returns:
        str: A confirmation message indicating the file was uploaded successfully,
             or an error message if an exception occurred during the process.
    """
    response_text = ""
    
    try:
        os.makedirs("temp", exist_ok=True)
        file_path = os.path.join("temp", filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
            
        s3.upload_file(file_path, bucket_name, filename)

        response_text = "file uploaded to "+bucket_name+"/"+filename
    except Exception as e:
        print(e)
        response_text = str(e)
    return response_text


@wasabi_mcp.tool(name = "delete_file")
def delete_file(bucket_name: str, key: str):
    """
    Deletes a specified file (object) from an S3-compatible storage bucket.

    This tool interacts directly with the S3 client to remove an object identified
    by its bucket name and key (path within the bucket).

    Args:
        bucket_name (str): The name of the S3 bucket from which the file is to be deleted.
                           (e.g., "my-documents-bucket").
        key (str): The unique identifier (key) of the object within the bucket. This
                   is essentially the full path to the file within the bucket
                   (e.g., "reports/annual_report_2024.pdf", "images/profile.jpg").

    Returns:
        dict: A dictionary indicating the outcome of the deletion operation.
              - On success: `{"message": "Successfully Deleted", "status": "Success"}`
              - On failure: `{"message": "Internal Server Error", "status": "Failure"}`
                            (along with error details printed to the console).
    """    
    print("IN wasabi delete file")
    response_data = {"message" : "Successfully Deleted", "status" :  "Success"}
    try:
        s3.delete_object(Bucket=bucket_name, Key=key)
    except Exception as e:
        response_data = {"message" : "Internal Server Error", "status" :  "Failure"}
        print(e)
    print("out wasabi delete file")
    return response_data

@wasabi_mcp.tool(name = "presigned_url")
def presigned_url(bucket_name: str, key: str, expires_in: int = 3600):
    """
    Generates a pre-signed URL for an S3 object, allowing temporary, time-limited access to it.

    This tool creates a URL that grants temporary access permissions to a specific
    object in an S3-compatible bucket without requiring AWS credentials. The generated
    URL is valid for a default duration of 1 hour (3600 seconds) but can be
    customized. This is useful for securely sharing private S3 objects with users
    who don't have direct S3 access.

    Args:
        bucket_name (str): The name of the S3 bucket where the object is located
                           (e.g., "my-data-archive").
        key (str): The unique identifier (key) of the object within the bucket for
                   which the pre-signed URL is to be generated (e.g., "documents/report.pdf").
        expires_in (int, optional): The number of seconds for which the pre-signed
                                    URL will be valid. Defaults to 3600 seconds (1 hour).

    Returns:
        dict: A dictionary containing the result of the operation.
              - On success: `{"message": "Successfully Generated", "status": "Success", "presigned_url": "..."}`
                            where "..." is the generated URL.
              - On failure: `{"message": "Internal Server Error", "status": "Failure"}`
                            (along with error details printed to the console).
    """

    print("In wasabi presigned url")
    response_data = {"message" : "Successfully Generated", "status" :  "Success"}
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )
        response_data["presigned_url"] = url
    except Exception as e:
        response_data = {"message" : "Internal Server Error", "status" :  "Failure"}
        print(e)
    print("out wasabi presigned url")
    return response_data

@wasabi_mcp.tool(name = "list_all_files")
def list_all_files(bucket_name: str):
    """
    Lists all file keys (names) present in a specified S3 bucket.

    This client-side function interacts with an S3-compatible service to retrieve
    a comprehensive list of all objects (files) stored within a given bucket.
    It uses a paginator to efficiently handle buckets containing a large number
    of objects, ensuring all keys are retrieved.

    Args:
        bucket_name (str): The name of the S3 bucket from which to list files
                           (e.g., "my-archive-data", "company-documents").

    Returns:
        list[str]: A list of strings, where each string is the full key (path and name)
                   of a file within the specified bucket (e.g., "folder/subfolder/document.pdf", "image.png").
                   Returns an empty list if the bucket is empty or if no 'Contents' are found.
    """
    return_list = []
    prefix = ""
    
    print("in list_all_files : ", bucket_name)
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    return_list.append(obj['Key'])
        
        print("return_list :: ", str(len(return_list)))
    except Exception as e:
        print("list_all_files : ", str(e))
        print(e)
    print(return_list)
    return return_list

@wasabi_mcp.tool(name = "file_content")
def file_content(bucket_name: str, file_key: str):
    """
    Reads and returns the content of a file from a specified S3 bucket,
    with specialized handling for different file types.

    This tool determines the file type based on its extension and uses
    appropriate helper functions to extract content from DOCX, PDF, and TXT files.
    For other file types, it retrieves the raw binary content directly from S3.

    Args:
        bucket_name (str): The name of the S3 bucket where the file is located
                           (e.g., "my-document-repo").
        file_key (str): The full key (path and name) of the file within the bucket
                        (e.g., "reports/latest/minutes.docx", "forms/application.pdf").

    Returns:
        str or bytes: The extracted content of the file.
                      - For DOCX, PDF, and TXT files, it attempts to return the
                        textual content as a string.
                      - For other file types, it returns the raw binary content of the file as bytes.
                      - In case of an error, it returns a string representation of the exception.
    """

    file_content = ""

    try:
        file_type = file_key.split(".")[-1]
        print(file_type)
        if file_type == "docx":
            file_content = wasabi_helper.read_docx_from_s3(bucket_name=bucket_name, object_key=file_key)
        elif file_type == "pdf":
            file_content = wasabi_helper.read_pdf_from_s3(bucket_name=bucket_name, object_key=file_key)
        elif file_type == "txt":
            file_content = wasabi_helper.read_txt_from_s3(bucket_name=bucket_name, object_key=file_key)
        else:
            response = s3.get_object(Bucket = bucket_name, Key = file_key)
            file_content = response['Body'].read()
    except Exception as e:
        print(e)
        file_content = str(e)
    
    return file_content

print("Tools Wasabi activated")