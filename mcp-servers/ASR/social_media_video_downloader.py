import requests
import time
import re
import uuid
import os
import threading
import asr_process
import config

headers = {
    "x-rapidapi-key": config.RAPID_API_KEY,
    "x-rapidapi-host": config.RAPID_HOST
    }

chunk_size = 50 * 1024 * 1024

def get_video(url):
    os.makedirs("temp", exist_ok=True)
    unique_name = str(uuid.uuid4())
    temp_file_name = unique_name+".mp4"
    tmp_file = "temp/"+temp_file_name
    
    file_title = ""
    
    try:
        querystring = { "url": url, "filename": tmp_file}

        download_check_loop = True
        try_count = 0
        
        urlx = ""

        video_data = {}
        while download_check_loop and try_count < 4:
            try:
                response = requests.get(config.RAPID_API_ENDPOINT, headers=headers, params=querystring)
                video_data = response.json()
                if video_data["title"] != "...":
                    download_check_loop = False
                else:
                    time.sleep(10)
            except Exception as e:
                print(e)
                time.sleep(10)
            print("try_count >>> " + str(try_count))
            try_count = try_count + 1
        
        video_title = video_data['title']
        file_title = re.sub(",'", "", video_title)    

        if "links" in video_data and len(video_data["links"])>0:
            if "youtube.com" in url or "youtu.be" in url:
                link_found_aval = {}
                for video in video_data["links"]:
                    if "hasVideo" in video and "hasAudio" in video:
                        if video["hasVideo"] == True & video["hasAudio"] == True:
                            link_found_aval[video["qualityLabel"]] = video['link']
                    elif "qualityLabel" in video:
                        link_found_aval[video["qualityLabel"]] = video['link']

                if "360p" in link_found_aval:
                    urlx = link_found_aval["360p"]
                    print("link quality >>> 360p")
                elif "480p" in link_found_aval:
                    urlx = link_found_aval["480p"]
                    print("link quality >>> 480p")
                elif "720p" in link_found_aval:
                    urlx = link_found_aval["720p"]
                    print("link quality >>> 720p")
                elif "1080p" in link_found_aval:
                    urlx = link_found_aval["1080p"]
                    print("link quality >>> 1080p")
                elif "240p" in link_found_aval:
                    urlx = link_found_aval["240p"]
                    print("link quality >>> 240p")

            else:
                urlx = video_data['links'][0]['link']
                for video in video_data["links"]:
                    if "quality" in video:
                        if video["quality"].startswith("video"):
                            urlx = video['link']
                            break
        if urlx:
            resp = requests.get(urlx, stream=True)
            with open(tmp_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size = chunk_size):
                    if chunk:
                        f.write(chunk) 
    except Exception as e:
        print(e)

    return {"tmp_file" : tmp_file , "file_title" : file_title, "temp_file_name" : temp_file_name, "unique_name" : unique_name}

# testing
# output_json = get_video("https://www.youtube.com/watch?v=ay_f4ViQ-Cs")
# print(output_json)

# run_loop = True
# while run_loop:
#     if output_json:
#         run_loop = False

# t1 = threading.Thread(target = asr_process.get_text, args=(output_json["tmp_file"], output_json["temp_file_name"]))
# t1.start()

