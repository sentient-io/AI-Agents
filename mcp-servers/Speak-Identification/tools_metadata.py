from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
import requests
import json
import re
import config
from datetime import datetime
import pytz
from video_metadata_manager import VideoMetaDataManager

metadata_mcp = FastMCP("Metadata Tools")

manager = VideoMetaDataManager(
    host=config.DB_HOST,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    db_name=config.DB_NAME,
    port=13306
)

X_RAPIDAPI_KEY = config.X_RAPIDAPI_KEY
GOOGLE_GEMINI_API_KEY = config.GOOGLE_GEMINI_API_KEY


class GeminiClient:
    def __init__(self, api_key: str, model_name: str, data: dict):
        self.api_key = api_key
        self.model_name = model_name
        self.data = data
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def get_response(self) -> str:
        prompt = f"""Based on the data provided, your task is to find the most relevant response to the query using the content available in the provided data. Your response should be concise yet comprehensive, ensuring that all necessary details are captured.

        Data: {self.data}
        Query: From the data provided, find the names of the peoples mentioned from the data. The response should be structured as a JSON array containing the unique names of the peoples. Give only the unique names from the data, do not include the similar names in the output. Also mention the title of the person if it is mentioned in the given data. Do not include any other information apart from the names of the peoples and their titles from the given data.

        Instructions:
        1. **Content Relevance**: Understand the query and collect the list of unique names of the peoples given in the data. Give only the unique names from the data, do not include the similar names in the output. Also mention the title of the person if it is mentioned in the given data. Do not include any other information apart from the names of the peoples and their titles from the given data.
        2. **Output Format**: The output must be in json array and the response must be a array of strings . Do not add like this text in output "```json\n" and "\n```". Do not add any invalid control character in JSON. Ensure the response is always structured as JSON and nothing else is included in the output. The output only contains the JSON array and nothing else. Do not add any explanation or additional text outside of the JSON array. The output should be a valid JSON array and nothing else. Do not add any invalid control character in JSON. Ensure the response is always structured as JSON and nothing else is included in the output. The output only contains the JSON array and nothing else. Do not add any explanation or additional text outside of the JSON array.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()


def get_clean_json(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
    return []

def get_youtube_id(url: str) -> str | None:
    regex = (
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    )
    match = re.search(regex, url)
    return match.group(1) if match else None


def get_youtube_metadata(video_url: str, rapidapi_key: str):
    video_id = get_youtube_id(video_url)
    cursor = ""
    all_comments = []
    headers = {
        'x-rapidapi-host': 'youtube138.p.rapidapi.com',
        'x-rapidapi-key': rapidapi_key
    }

    data = {}
    video_details_url = f"https://youtube138.p.rapidapi.com/video/details/?id={video_id}"
    video_response = requests.request("GET", video_details_url, headers=headers)
    print(video_response)
    if video_response.status_code == 200:
        video_data = video_response.json()
        data['video_id'] = video_id
        data['created_by'] = video_data.get('author', {}).get('title', '')
        data['created_date'] = video_data.get('publishedDate', '')
        data['title'] = video_data.get('title', '')
        data['description'] = video_data.get('description', '')
        data['keywords'] = video_data.get('keywords', [])
        data['likes'] = video_data.get('stats', {}).get('likes', '')
        data['view_count'] = video_data.get('stats', {}).get('views', '')        

    try:
        only_comments = data.get('description', '')
        return (data, only_comments)
    except Exception as e:
        return None


def get_facebook_metadata(video_url: str, rapidapi_key: str):
    detail_url = f"https://facebook-scraper-api4.p.rapidapi.com/get_facebook_post_details?link={video_url}"
    payload = {}
    headers = {
        'x-rapidapi-key': rapidapi_key,
        'x-rapidapi-host': 'facebook-scraper-api4.p.rapidapi.com'
    }
    metadata = {}
    detail_response = requests.request("GET", detail_url, headers=headers, data=payload)
    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        if len(detail_data) > 0:
            detail_data = detail_data[0]
            metadata['video_id'] = detail_data.get('details', {}).get('post_id', '')
            metadata['title'] = detail_data.get('values', {}).get('text', '')
            metadata['created_by'] = detail_data.get('user_details', {}).get('name', '')
    if metadata:
        return (metadata, metadata.get('title', ''))
    else:
        return None

def get_tiktok_metadata(video_url: str, rapidapi_key: str):
    detail_url = f"https://tiktok-scraper7.p.rapidapi.com/?url={video_url}"
    payload = {}
    headers = {
        'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com',
        'x-rapidapi-key': rapidapi_key,
    }
    metadata = {}
    detail_response = requests.request("GET", detail_url, headers=headers, data=payload)

    if detail_response.status_code == 200:
        detail_data = detail_response.json()['data']
        metadata["video_id"] = detail_data.get('id', '')
        metadata['title'] = detail_data.get('title', '')
        metadata['created_by'] = detail_data.get('author', {}).get('unique_id', '')
        metadata['created_date'] = detail_data.get('create_time', '')

    if metadata:
        return (metadata, metadata.get('title', ''))
    else:
        return None

@metadata_mcp.tool( name = "get_metadata_info" )
def get_metadata_info(url: str):
    """
    Retrieves metadata and processes comments from a given social media URL (YouTube, Facebook, or TikTok).

    This tool fetches video or post metadata, including comments, from the specified URL.
    It then analyzes the comments to identify potential 'speakers' (which could be key entities
    or people mentioned). Finally, it cleans and formats the top 10 comments and includes the identified speakers in the output data.

    Args:
        url (str): The URL of the social media post or video (must contain 'youtube.com',
                   'youtu.be', 'facebook.com', or 'tiktok.com').

    Returns:
        dict: A dictionary containing the processing status, a message, and the 'data' payload.
              The 'data' includes the original metadata, a 'comments' list (top 10 cleaned comments),
              and a 'speakers' list (identified by the AI model).
              
              Example Success Return:
              {"status": "Success", "data": {... metadata ..., "comments": [...], "speakers": [...]}, "message": "Successfully processed."}
              
              Example Failure Return:
              {"status": "Success", "message": "Not able to fetch metadata."}
    """    
    existing_data = manager.get_video_metadata(url)
    print(existing_data)
    if existing_data is None:
        rapidapi_key = X_RAPIDAPI_KEY
        coment_response = None
        if "youtube.com" in url or "youtu.be" in url:
            print("IN youtube")
            coment_response = get_youtube_metadata(url, rapidapi_key)
            print(coment_response)
            print("out youtube")
        elif "facebook.com" in url:
            print("Fetching Facebook comments...")
            coment_response = get_facebook_metadata(url, rapidapi_key)
        elif "tiktok.com" in url:
            coment_response = get_tiktok_metadata(url, rapidapi_key)
        
        metadata_template = {
                "video_id": "",
                "title": "",
                "description": "",
                "duration": "",
                "file_info": 
                {
                    "filename": "",
                    "format": "",
                    "codec": ""
                },
                "content":
                {
                    "keywords": []
                },
                "people":
                {
                    "speakers":[]
                },
                "usage":
                {
                    "view_count": "",
                    "likes": "",
                    "owner": "",
                    "analysis_timestamp": ""
                }
            }        
        if coment_response:
            data, only_comments = coment_response
            metadata_template['video_id'] = data.get('video_id', '')
            metadata_template['title'] = data.get('title', '')
            metadata_template['description'] = data.get('description', '')
            metadata_template['duration'] = ""
            metadata_template['file_info']['filename'] = data.get('title', '')
            metadata_template['file_info']['format'] = 'mp4'
            metadata_template['file_info']['codec'] = 'H.264'
            metadata_template['content']['keywords'] = data.get('keywords', [])
            metadata_template['usage']['view_count'] = data.get('view_count', '')
            metadata_template['usage']['likes'] = data.get('likes', '')
            metadata_template['usage']['owner'] = data.get('created_by', '')
            sg_timezone = pytz.timezone('Asia/Singapore')
            sg_time = datetime.now(sg_timezone)
            formatted_time = sg_time.strftime("%d/%m/%Y %I:%M %p").lower()
            metadata_template['usage']['analysis_timestamp'] = formatted_time +" SGT" # data.get('created_date', '')

            client = GeminiClient(
                api_key=GOOGLE_GEMINI_API_KEY,
                model_name="gemini-2.0-flash",
                data=only_comments
            )
            gemini_response = client.get_response()
            speakers = get_clean_json(gemini_response)

            for speaker in speakers:
                metadata_template['people']['speakers'].append({'name': speaker})

            try:
                video_id = metadata_template['video_id']
                manager.insert_video_data(video_id, url, metadata_template)
            except Exception as e:
                print(e)
            return {"status": "Success", "data": metadata_template, "message": "Successfully processed."}
        else:
            return {"status": "Success", "message": "Not able to fetch metadata."}
    else:
        return {"status": "Success", "data": existing_data, "message": "Successfully processed."}
    
print("Metadata Tools Activated")