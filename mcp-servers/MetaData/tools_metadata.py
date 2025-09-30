from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
import requests
import json
import re
import config

metadata_mcp = FastMCP("Metadata Tools")


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
        Query: From the data provided, find the names of the peoples mentioned from the data. The response should be structured as a JSON array containing the names of the peoples. Also mention the title of the person if it is mentioned in the given data. Do not include any other information apart from the names of the peoples and their titles from the given data.

        Instructions:
        1. **Content Relevance**: Understand the query and collect the list of names of the peoples given in the data. Also mention the title of the person if it is mentioned in the given data. Do not include any other information apart from the names of the peoples and their titles from the given data.
        2. **Output Format**: The output must be in json array and the response must be a array of strings . Do not add like this text in output "```json\n" and "\n```". Do not add any invalid control character in JSON. Ensure the response is always structured as JSON and nothing else is included in the output. The output only contains the JSON array and nothing else. Do not add any explanation or additional text outside of the JSON array. The output should be a valid JSON array and nothing else. Do not add any invalid control character in JSON. Ensure the response is always structured as JSON and nothing else is included in the output. The output only contains the JSON array and nothing else. Do not add any explanation or additional text outside of the JSON array.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()


def get_youtube_id(url: str) -> str | None:
    regex = (
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    )
    match = re.search(regex, url)
    return match.group(1) if match else None


def get_youtube_comments(video_url: str, rapidapi_key: str):
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
    if video_response.status_code == 200:
        video_data = video_response.json()
        data['video_id'] = video_id
        data['created_by'] = video_data.get('author', {}).get('title', '')
        data['created_date'] = video_data.get('publishedDate', '')
        data['title'] = video_data.get('title', '')
        data['description'] = video_data.get('description', '')
        data['keywords'] = video_data.get('keywords', [])

    while True:
        url = f"https://youtube138.p.rapidapi.com/video/comments/?id={video_id}"
        if cursor:
            url += f"&cursor={cursor}"
        
        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
            comment_data = response.json()
            comments = comment_data.get('comments', [])
            all_comments.extend(comments)
            cursor = comment_data.get('cursorNext', '')
            if not cursor:
                break
            
        # else:
        #     break
    
    try:
        comments = []
        only_comments = [cmt.get('content', '') for cmt in all_comments]
        for cmt in all_comments:
            comment = cmt.get('content', '')
            author = cmt.get('author', {}).get('title', '')
            comments.append({'comment': comment, 'name': author})
        data['comments'] = comments
        return (data, only_comments)
    except Exception as e:
        return None


def get_facebook_comments(video_url: str, rapidapi_key: str):
    url = f"https://facebook-scraper-api4.p.rapidapi.com/get_facebook_post_comments_details?link={video_url}"
    print(url, rapidapi_key)
    payload = {}
    headers = {
        'x-rapidapi-key': rapidapi_key,
        'x-rapidapi-host': 'facebook-scraper-api4.p.rapidapi.com'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        print(response.text)
        try:
            data = response.json()
            only_comments = [i['comment_text'] for i in data['data']['comments']]
            comments = [{'comment': i['comment_text'], 'name': i['author']['name']} for i in data['data']['comments']]
            fb_response = {
                'created_by': "",
                'created_date': "",
                'comments': comments
            }
            return (fb_response, only_comments)
        except Exception as e:
            print(f"Error parsing Facebook comments: {e}")
            return None
    else:
        print(f"Facebook API request failed with status code {response.status_code}")
        print(response.text)
        return None


def get_tiktok_comments(video_url: str, rapidapi_key: str):
    url = f"https://tiktok-scraper7.p.rapidapi.com/comment/list?url={video_url}"
    payload = {}
    headers = {
        'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com',
        'x-rapidapi-key': rapidapi_key,
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            data = response.json()
            only_comments = [i['text'] for i in data['data']['comments']]
            comments = [{'comment': i['text'], 'name': i['user']['unique_id']} for i in data['data']['comments']]
            tt_response = {
                'created_by': "",
                'created_date': "",
                'comments': comments
            }
            return (tt_response, only_comments)
        except Exception as e:
            print(f"Error parsing TikTok comments: {e}")
            return None
    else:
        return None

#MCP Call
@metadata_mcp.tool( name = "get_comments" )
def get_social_media_comments(url: str, doc_id: str):
    rapidapi_key = X_RAPIDAPI_KEY
    if "youtube.com" in url or "youtu.be" in url:
        coment_response = get_youtube_comments(url, rapidapi_key)
    elif "facebook.com" in url:
        print("Fetching Facebook comments...")
        coment_response = get_facebook_comments(url, rapidapi_key)
    elif "tiktok.com" in url:
        coment_response = get_tiktok_comments(url, rapidapi_key)
    else:
        return None
    
    if coment_response:
        data, only_comments = coment_response
        client = GeminiClient(
            api_key=GOOGLE_GEMINI_API_KEY,
            model_name="gemini-2.0-flash",
            data=only_comments
        )
        gemini_response = client.get_response()
        try:
            speakers = json.loads(gemini_response)
        except json.JSONDecodeError:
            speakers = []

        comments = data.get('comments', [])
        cleaned_comments = []
        if comments:
            for i in comments[:10]:
                cleaned_text = re.sub(r'[\U00010000-\U0010FFFF]', '', i['comment'])
                cleaned_comments.append({'comment': cleaned_text, 'name': i['name']})
            data['comments'] = cleaned_comments
        data['speakers'] = speakers

        return {"status": "Success", "data": data, "message": "Successfully Got the Comments."}
    else:
        return None
    
print("Metadata Tools Activated")