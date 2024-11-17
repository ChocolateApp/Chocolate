import os
import requests

directory = r'G:\Projets\Chocolate\src\chocolate\static\lang'
api_url_template = "https://hosted.weblate.org/api/translations/chocolate/{component}/{lang}/file/"
token = os.environ.get("WEBLATE_TOKEN")
author_name = "imprevisible"
author_email = "impr.visible@gmail.com"
upload_method = "translate"
conflit = "ignore"
fuzzy = "process"

def upload_file_to_weblate(file_path, component, lang):
    headers = {
        "Authorization": f"Token {token}"
    }

    url = api_url_template.format(component=component, lang=lang)
    with open(file_path, 'rb') as file:
        form = {
            'file': (os.path.basename(file_path), file),
            'email': author_email,
            'author': author_name,
        }
        data = {
            'message': upload_method,
            'conflict': conflit,
            'fuzzy': fuzzy,
        }
        response = requests.post(url, headers=headers, files=form, data=data)

    if response.status_code == 200:
        print(f"Uploaded {file_path} to Weblate for language {lang} ({response.text})")
    else:
        print(f"Failed to upload {file_path} to Weblate for language {lang}. Status code: {response.status_code}")
        print(response.text)
        print(response)

def process_files_in_directory(directory):
    component = "translation"  # Replace with the actual component slug
    lang_files = [file for file in os.listdir(directory) if file.endswith('.json')]
    for lang_file in lang_files:
        file_path = os.path.join(directory, lang_file)
        lang = os.path.splitext(lang_file)[0]
        print(f"Processing {file_path} for language {lang}")
        upload_file_to_weblate(file_path, component, lang)

if __name__ == "__main__":
    process_files_in_directory(directory)
