import requests

url = "http://127.0.0.1:5000/upload-file"

files = {
    "file": open("sample.png", "rb")
}

response = requests.post(url, files=files)

print(response.status_code)
print(response.json())