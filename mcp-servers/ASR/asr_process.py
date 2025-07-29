import os
import magic
import requests
import json
import time
import config

def get_text(file_path, file_name):
    print("file_path : ", file_path)
    print("file_name : ", file_name)
    fileSize = os.path.getsize(file_path)
    content_type = magic.from_file(file_path, mime=True)

    asr_output_data = {}
    data = {
        "file_name": file_name, 
        "file_size" : fileSize, 
        "content_type" : content_type, 
        "additional_param" : {
            "language": "",
            "model_type": "large-v2"
        }
    }    

    headers= {'x-api-key': config.SENTIENT_X_API_KEY}

    res = requests.request("POST", config.ASR_UPLOAD_ENDPOINT, json=data, headers=headers)

    res_data = json.loads(res.text)

    print(res_data)
    if "results" in res_data :
        res_data = res_data['results']
        jid = res_data["jid"]

        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            requests.post(res_data['url'], data = res_data['fields'], files = files)
        
        process_done = False

        STATUS_API_ENDPOINT = config.ASR_STATUS_ENDPOINT+jid
        while not process_done:
            time.sleep(10)
            asrResponce = requests.request("GET",STATUS_API_ENDPOINT, headers=headers)

            asr_data = json.loads(asrResponce.text)

            if asr_data["status"] == "Success" :
                process_done = True
                output_url = asr_data["output_url"]
                response = requests.request("GET", output_url)
                data_json = response.text
                asr_output_data = json.loads(data_json)

                json_output_filename = file_path.replace(".mp4", ".json")

                with open(json_output_filename, 'w', encoding='utf-8') as f:
                            json.dump(asr_output_data, f, ensure_ascii=False, indent=4)

    else:
        print("jid not found")

    return asr_output_data