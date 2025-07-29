from fastapi import UploadFile, File
from mcp.server.fastmcp import FastMCP
import social_media_video_downloader
import asr_process
import threading

# Create FastMCP instance and define tools
asr_mcp = FastMCP("ASR Tools")

@asr_mcp.tool(name = "transcribe")
def transcribe(url: str) -> str:
    """Transcribe from URL."""
    sm_data = social_media_video_downloader.get_video(url)
    response_str = ""
    if "unique_name" in sm_data:
        if sm_data["unique_name"]:
            # response_str = "URL title : "+ sm_data["file_title"] + " and refrence ID : "+sm_data["unique_name"]+ " . Keep this refrence ID and check after 5 mins for your transcribe data."
            asr_response_data = asr_process.get_text(sm_data["tmp_file"], sm_data["temp_file_name"])
            # threading_session = threading.Thread(target = asr_process.get_text, args=(sm_data["tmp_file"], sm_data["temp_file_name"]))
            # threading_session.start()
            response_str = asr_response_data["results"]["text"]
        else:
            response_str = "Error try again latter."
    else:
        response_str = "Error try again latter."
    
    print(response_str)

    return response_str