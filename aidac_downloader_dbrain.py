import requests
import argparse
import os
import json
import hashlib
from tqdm import tqdm
import numpy as np
import cv2
import base64
import img2pdf
import zipfile
import soundfile as sf
import shutil
from datetime import datetime
from typing import Dict, List, Any
import glob

conversation_categories = {
    "1a": "Greetings and Small Talk",
    "1b": "Conversation Practice",
    "1c": "Virtual Companionship",
    "1d": "Sharing Personal Experiences",
    "1e": "Emotional Support",
    "2a": "Jokes and Fun",
    "2b": "Storytelling",
    "2c": "Music and Songs",
    "2d": "Games and Trivia",
    "2e": "Entertainment and Movie Information",
    "2f": "Sports",
    "3a": "Knowledge and Information Retrieval",
    "3b": "Educational Assistance",
    "3c": "Language Learning and Translation",
    "4a": "Work & Collaboration",
    "4b": "Technical Support & Coding",
    "5a": "Health and Fitness",
    "5b": "Mental Health Support",
    "5c": "Food and Recipe Assistance",
    "5d": "Medical Advice and Health Guidance",
    "5e": "Animals and Pets",
    "6a": "Directions & Maps",
    "6b": "Travel Recommendations",
    "7a": "Financial Management",
    "8a": "Shopping and Recommendations",
    "8b": "Grocery Lists & Shopping",
    "8c": "DIY Help",
    "9a": "Content Creation",
    "9b": "Creative Writing & Art",
    "9c": "Music Composition",
    "10a": "FAQ Handling",
    "10b": "Product Assistance",
    "11a": "Voice-to-Text Transcription",
    "11b": "Simplifying Information",
    "11c": "Assistance for Visually Impaired",
    "12a": "Contract Explanations",
    "12b": "Policy Summaries",
    "12c": "Legal Research Assistance",
    "13a": "Environmental Science and Ecology",
    "14a": "Conversations that involve wired human sounds & direct audio playing from users"
}

conversation_categories_remapped = {
    "1a": "Greetings and Small Talk",
    "1b": "Conversation Practice",
    "1c": "Virtual Companionship",
    "1d": "Sharing Personal Experiences",
    "1e": "Emotional Support",
    "2a": "Jokes and Fun",
    "2b": "Storytelling",
    "2c": "Music and Songs",
    "2d": "Games and Trivia",
    "2e": "Entertainment and Movie Information",
    "2f": "Sports",
    "3a": "Knowledge and Information Retrieval",
    "3b": "Educational Assistance",
    "3c": "Language Learning and Translation",
    "4a": "Work & Collaboration",
    "4b": "Technical Support & Coding",
    "5a": "Health and Fitness",
    "5b": "Mental Health Support",
    "5c": "Food and Recipe Assistance",
    "5d": "Medical Advice and Health Guidance",
    "5e": "Animals and Pets",
    "6a": "Directions & Maps",
    "6b": "Travel Recommendations",
    "7a": "Financial Management",
    "8a": "Shopping and Recommendations",
    "8b": "Grocery Lists & Shopping",
    "8c": "DIY Help",
    "9a": "Content Creation",
    "9b": "Creative Writing & Art",
    "9c": "Music Composition",
    "10a": "FAQ Handling",
    "10b": "Product Assistance",

    "11a": "FAQ Handling",  # Duplicate of 10a (document has Customer Support twice)
    "11b": "Product Assistance",  # Duplicate of 10b (document has Customer Support twice)
    "12a": "Voice-to-Text Transcription",
    "12b": "Simplifying Information",
    "12c": "Assistance for Visually Impaired",
    "13a": "Contract Explanations",
    "13b": "Policy Summaries",
    "13c": "Legal Research Assistance",
    "14a": "Environmental Science and Ecology",
    "15a": "Conversations that involve wired human sounds & direct audio playing from users"
}


import csv

def csv_to_dict(filename):
    """
    Converts a CSV file to a dictionary.
    
    Args:
        filename (str): Path to the CSV file
        
    Returns:
        dict: Dictionary where the 2nd column of each row is the key and
              the 1st column is the value
    """
    result_dict = {}
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if len(row) >= 2:  # Ensure row has at least 2 entries
                    value = row[0]  # 1st entry as value
                    key = row[1]    # 2nd entry as key
                    result_dict[key] = value
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return result_dict


def is_object_rejected(uploads):

    rejected_list = [
        upload for upload in uploads
        if upload['approvalStatus'] == 0
    ]

    return True if len(rejected_list) else False

def get_reject_count(uploads):

    rejected_list = [
        upload for upload in uploads
        if upload['approvalStatus'] == 0
    ]

    return len(rejected_list)

def get_approved_count(uploads):

    approved_list = [
        upload for upload in uploads
        if upload['approvalStatus'] == 2
    ]

    return len(approved_list)


def is_object_pending (uploads):

    pending_list = [
        upload for upload in uploads
        if upload['approvalStatus'] == 1
    ]

    return True if len(pending_list) else False


def create_folder(folder_name):

    isExist = os.path.exists(folder_name)
    if not isExist:
        os.makedirs(folder_name)

def file_already_present(file_path, upload_md5):

    isExist = os.path.exists(file_path)
    if not isExist:
        return False

    if os.path.getsize(file_path) > 0:
        return True
    else:
        return False

    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

    md5_returned = file_hash.hexdigest()

    return True if md5_returned == upload_md5 else False

def download_file(url: str, fname: str, chunk_size=1024):
    resp = requests.get(url, stream=True)
    if resp.status_code != 200:
        print('Download failed, response code =', resp.status_code)
        return False

    total = int(resp.headers.get('content-length', 0))
    with open(fname, 'wb') as file, tqdm(
        desc=fname,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

    return True

def convert_b64_to_png(signature_b64):

   encoded_data = signature_b64.split(',')[1]
   nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

   return img

def insert_signature(img, signature_b64, x_pos, y_pos):
    font = cv2.FONT_HERSHEY_COMPLEX

    #y_pos += y_off + 50
    text = "Signature : " 
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    signature_png = convert_b64_to_png(signature_b64)

    signature_png = cv2.resize(signature_png, (0, 0), fx = 0.2, fy = 0.2)

    trans_mask = signature_png[:,:,3] == 0
    signature_png[trans_mask] = [255, 255, 255, 255]
    signature_png = cv2.cvtColor(signature_png, cv2.COLOR_BGRA2BGR)

    x_pos = 350
    y_pos -= 80
    sign_height, sign_width, _ = signature_png.shape

    img[y_pos:y_pos+sign_height, x_pos:x_pos+sign_width] = signature_png

    return img

def generate_consent_form(consent_form_data, project_name, task_name, output_path, cf_id):
    
    img = np.ones((1920, 1080, 3), dtype = np.uint8)
    img = 255*img

    text = "CONSENT FORM"
    font = cv2.FONT_HERSHEY_COMPLEX

    # get boundary of this text
    textsize = cv2.getTextSize(text, font, 1, 2)[0]

    # get coords based on boundary
    x_pos = int((img.shape[1] - textsize[0]) / 2)
    y_pos = 100

    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    x_pos = 100
    y_pos += 100
    y_off = 80

    text = "Project Name : " + project_name
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Task Name : " + task_name
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    for item in consent_form_data:
        y_pos += y_off
        if 'signature' in item['name'].lower():
            img = insert_signature(img, item['value'], x_pos, y_pos)
        else:
            text = item['name'] + ':     ' + item['value']
            cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    jpg_file_name = output_path + '/consent_form.jpg'

    cv2.imwrite(jpg_file_name, img)

    pdf_file_name = output_path + '/consent_form_'+str(cf_id)+'.pdf'

    with open(pdf_file_name,"wb") as f:
        f.write(img2pdf.convert(jpg_file_name))

    os.remove(jpg_file_name)

def is_zip_file(filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_file:
            # If the file opens successfully, it is a zip file
            return True
    except (zipfile.BadZipFile, FileNotFoundError):
        # If an exception occurs, it's not a zip file or the file doesn't exist
        return False

def is_flac_file(filepath):
    try:
        with open(filepath, 'rb') as file:
            # Read the first 4 bytes of the file
            header = file.read(4)
            # Check if the bytes match the FLAC signature
            return header == b'fLaC'
    except FileNotFoundError:
        # File does not exist
        return False
    except Exception as e:
        # Handle other potential errors
        print(f"An error occurred: {e}")
        return False

def unzip_file(zip_filepath):
    try:

        extract_to_folder = os.path.dirname(zip_filepath) + '/temp'

        # Create the directory to extract to if it doesn't exist
        os.makedirs(extract_to_folder, exist_ok=True)
        
        # Open the zip file
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            # Extract all contents to the specified directory
            zip_ref.extractall(extract_to_folder)

        src_file = extract_to_folder + '/' + os.path.basename(zip_filepath)

        shutil.copyfile(src_file, zip_filepath) #dst file name is same as the zip file

        shutil.rmtree(extract_to_folder)
    except Exception as e:
        print(f"An error occurred: {e}")

def convert_flac_to_wav(input_filepath):
    try:

        output_filepath = input_filepath
        input_filepath = input_filepath+'.flac'
        os.rename(output_filepath, input_filepath)
        # Read the FLAC file
        data, samplerate = sf.read(input_filepath)
        # Write the data to a WAV file
        sf.write(output_filepath, data, samplerate)
        os.remove(input_filepath)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_acoustic_environments(csv_file_path):
    """
    Process a CSV file to extract Upload Id and corresponding acoustic environment.
    
    Args:
        csv_file_path (str): Path to the CSV file
        
    Returns:
        dict: Dictionary with Upload Id as key and CM_AcousticEnvironment as value
    """
    result = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                upload_id = row.get("Upload Id", "")
                acoustic_env = row.get("CM_AcousticEnvironment", "")
                
                if upload_id:  # Only add if upload_id exists
                    result[upload_id] = acoustic_env
    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        
    return result

import csv

def create_csv_from_nested_dict(nested_dict, headers, file_path):
    """
    Create a CSV file from a nested dictionary structure with specified headers.
    
    Args:
        nested_dict (dict): Dictionary where values are dictionaries containing data
        headers (list): List of column headers to include and their order
        file_path (str): Path where the CSV file will be saved
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Write the header row
            writer.writeheader()
            
            # Write each person's data as a row
            for person_id, person_data in nested_dict.items():
                # Only include fields that are in the headers list
                row_data = {key: person_data.get(key, '') for key in headers}
                writer.writerow(row_data)
                
        print(f"CSV file successfully created at {file_path}")
    except Exception as e:
        print(f"Error creating CSV file: {e}")


def get_value_by_name(json_data, name):
    """
    Get the value associated with a specific name from a JSON list of dictionaries.
    
    Args:
        json_data: A list of dictionaries, each with 'id', 'name', and 'value' keys
        name: The name to search for
        
    Returns:
        The value associated with the name, or None if not found
    """
    for item in json_data:
        if item.get('name') == name:
            return item.get('value')
    return None


def speaker_map_csv_to_json(csv_file_path: str) -> Dict[str, List[Any]]:
    """
    Reads a CSV file and converts it to a JSON format where:
    - The first column values are used as keys
    - The rest of the columns for each row are converted to a list and stored as values
    
    Args:
        csv_file_path (str): Path to the input CSV file
        
    Returns:
        Dict[str, List[Any]]: Dictionary with the converted data or an empty dict if file not found
    """
    result = {}
    
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:  # Skip empty rows
                    continue
                    
                key = row[0]
                values = row[1:] if len(row) > 1 else []
                result[key] = values
    except FileNotFoundError:
        # Return empty dictionary if file doesn't exist
        return {}
    
    return result

def speaker_map_json_to_csv(json_data: Dict[str, List[Any]], csv_file_path: str) -> None:
    """
    Converts JSON data to CSV format where:
    - Each key becomes the first column in a row
    - The list of values becomes the rest of the columns in that row
    
    Args:
        json_data (Dict[str, List[Any]]): Dictionary to convert
        csv_file_path (str): Path to save the CSV output
        
    Returns:
        None
    """
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for key, values in json_data.items():
            # Ensure values is a list
            if not isinstance(values, list):
                values = [values]
            
            # Write key and values to CSV
            writer.writerow([key] + values)


def create_empty_file(filename):
    with open(filename, 'w') as f:
        pass  # Do nothing, just create the file


import json
from collections import defaultdict

def count_user_ids_from_uploads(json_data):
    """
    Counts how many times each userId appears inside uploads.

    Parameters:
    - json_data (dict): JSON with "objects" → "uploads" → each having a "userId".

    Returns:
    - dict: {userId: count}
    """
    user_id_counts = defaultdict(int)

    for obj in json_data.get("objects", []):
        for upload in obj.get("uploads", []):
            user_id = upload.get("userId")
            approval_status = upload.get("approvalStatus")

            if user_id is not None:
                if approval_status == 2:
                    user_id_counts[user_id] += 1

    return dict(user_id_counts)


def get_json_data(folder_path):
    """
    Finds and unzips a file with prefix 'aidas_json_project-1' in the specified folder,
    then returns the content of the JSON file found within.
    
    Args:
        folder_path (str): Path to the folder containing the zip file
        
    Returns:
        dict: The parsed JSON data
        
    Raises:
        FileNotFoundError: If no zip file with the required prefix is found
        FileNotFoundError: If no JSON file is found in the extracted contents
    """
    # Find zip file with the specific prefix
    zip_pattern = os.path.join(folder_path, "aidas_json_project-1*.zip")
    zip_files = glob.glob(zip_pattern)
    
    if not zip_files:
        raise FileNotFoundError(f"No zip file with prefix 'aidas_json_project-1' found in {folder_path}")
    
    # Use the first matching zip file
    zip_file_path = zip_files[0]
    
    # Create extraction directory
    extract_dir = os.path.join(folder_path, "extracted_content")
    os.makedirs(extract_dir, exist_ok=True)
    
    # Unzip the file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Find JSON file
    json_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        raise FileNotFoundError(f"No JSON file found in the extracted contents")
    
    # Read the JSON file (using the first one found)
    with open(json_files[0], 'r') as f:
        json_data = json.load(f)
    
    return json_data

# Example usage:
# data = process_aidas_project("/path/to/folder")

def get_metadata_csv(folder_path):
    """
    Finds and unzips a file with prefix 'aidas_metadata-1' in the specified folder,
    then returns the path to the CSV file found within.
    
    Args:
        folder_path (str): Path to the folder containing the zip file
        
    Returns:
        str: Path to the extracted CSV file
        
    Raises:
        FileNotFoundError: If no zip file with the required prefix is found
        FileNotFoundError: If no CSV file is found in the extracted contents
    """
    # Find zip file with the specific prefix
    zip_pattern = os.path.join(folder_path, "aidas_metadata-1*.zip")
    zip_files = glob.glob(zip_pattern)
    
    if not zip_files:
        raise FileNotFoundError(f"No zip file with prefix 'aidas_metadata-1' found in {folder_path}")
    
    # Use the first matching zip file
    zip_file_path = zip_files[0]
    
    # Create extraction directory
    extract_dir = os.path.join(folder_path, "extracted_metadata")
    os.makedirs(extract_dir, exist_ok=True)
    
    # Unzip the file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Find CSV file
    csv_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in the extracted contents")
    
    # Return the path to the first CSV file found
    return csv_files[0]

# Example usage:
# csv_path = extract_aidas_metadata_csv("/path/to/folder")
# df = pd.read_csv(csv_path)  # You can then use pandas to read the CSV

def main():
    parser = argparse.ArgumentParser(description="AIDAC Downloader - Download dataset directly from cloud storage.")
    
    # Add command line arguments
    parser.add_argument("-r", "--release-folder-path", type=str, help="Release folder path", required=True)
    parser.add_argument("-i", "--ignore-rejected", action='store_true', help="Ignore and do not download rejected datasets")
    parser.add_argument("-l", "--language", type=str, help="Language", required=True)
    parser.add_argument("-d", "--dry-run", action='store_true', help="Dry run - do not download any files")

    args = vars(parser.parse_args())

    release_folder_path = args['release_folder_path']
    ignore_rejected = args['ignore_rejected']
    language =  args['language']
    dry_run = args['dry_run']

    download_data = None

    download_data = get_json_data(release_folder_path)
    metadata_csv = get_metadata_csv(release_folder_path)
    script_csv_filename = release_folder_path + '/' + language + '_Scripts.csv'
    user_upload_approval_count = count_user_ids_from_uploads(download_data)

    print(user_upload_approval_count)

    # Example usage:
    script_map = csv_to_dict(script_csv_filename)

    acoustic_environments_map = get_acoustic_environments(metadata_csv)

    project_id = download_data['id']
    project_name = download_data['name']
    is_grouping = download_data['groupingProject']

    consent_form_enabled = False
    if 'consentFormStatus' in download_data.keys():
        consent_form_enabled = True if download_data['consentFormStatus'] else False

    save_individual_recordings = False 
    if 'saveIndividualRecordings' in download_data.keys():
        save_individual_recordings = download_data['saveIndividualRecordings']

    tasks = download_data['objects']

    project_prefix = 'aidac/'+language+'/'
    approve_prefix = 'qc_approved/'
    reject_prefix = 'qc_rejected/'
    pending_prefix = 'qc_pending/'

    print('\n******************************************************************')
    print(' AIDAC Downloader - Downloads dataset and generates consent forms')
    print('******************************************************************\n')
 
    download_error = False

    user_id_map = {}
    current_user_id = None
    metadata_header = ['ID', 'Mobile Number', 'Language', 'Native Language', 'Accent', 'Age', 'Gender', 'Recording Device', 'Acoustic Environment 1', 'Acoustic Environment 2']
    metadata_data = {}
    metadata_folder = None

    #user_id, email, speaker_id, delivered

    db_file_name = language+'_db.csv'
    speaker_map_csv = speaker_map_csv_to_json(db_file_name)
    new_users_from_this_release = {}

    speaker_id = 1
    if len(speaker_map_csv):
        last_key = list(speaker_map_csv.keys())[-1]
        speaker_id = int(speaker_map_csv[last_key][1]) + 1

    for task in tasks:
        task_id = task['id']
        task_name = task['name']
        obj_uploads = task['uploads']

        consent_form_saved = False
        object_rejected = False        
        object_pending = False        
        if is_grouping:
            object_rejected = is_object_rejected(obj_uploads)
            object_pending = is_object_pending(obj_uploads)
            total_rejected = get_reject_count(obj_uploads)
            approved_count = get_approved_count(obj_uploads)

        if ignore_rejected and object_rejected:
            if total_rejected > 2: #Dbran specific, only 15 is required
                print('Ignoring rejected set')
                continue

        user_name = None 
        speaker_id_str = None
        user_id = None
        task_skipped = False


        for idx, upload in enumerate(obj_uploads):
            upload_id = upload['id']
            upload_file_name = upload['fileName']
            upload_url = upload['s3Url']
            upload_md5 = upload['md5']
            upload_approval_status = upload['approvalStatus']
            user_id = upload['userId']
            user_name = upload['userName']

            if acoustic_environments_map[str(upload_id)].strip() == '':
                print('Skipping empty metadata upload... UserId = ', user_id, 'Email = ', user_name)
                task_skipped = True
                continue

            if user_upload_approval_count[user_id] < 15:
                print('User ', user_id, ' has only ', approved_count, ' approved uploads, Skipping.')
                task_skipped = True
                continue

            if user_id in speaker_map_csv:
                if int(speaker_map_csv[user_id][2]) >= 16:
                    print('Skipping already delivered upload..')
                    task_skipped = True
                    continue

            if user_id != current_user_id:
                if user_id not in user_id_map:
                    formatted_speaker_id = f"{speaker_id:05d}"  
                    user_id_map[user_id] = [formatted_speaker_id, 0]
                    metadata_data[formatted_speaker_id] = {}
                    speaker_id += 1

            speaker_id_str = user_id_map[user_id][0]

            metadata_data[speaker_id_str]['ID'] = str(speaker_id_str)
            metadata_data[speaker_id_str]['Mobile Number'] = '+91 1234567890'
            metadata_data[speaker_id_str]['Language'] = language
            metadata_data[speaker_id_str]['Native Language'] = language
            metadata_data[speaker_id_str]['Accent'] = language

            # if object_rejected:
            #     folder_name = project_prefix + reject_prefix
            # elif object_pending:
            #     folder_name = project_prefix + pending_prefix
            # else:
            #     folder_name = project_prefix + approve_prefix

            folder_name = project_prefix
            metadata_folder = folder_name
            folder_name += '/' + speaker_id_str + '/'

            create_folder(folder_name)

            user_id_map[user_id][1] += 1
            file_cnt = user_id_map[user_id][1]
            file_cnt_str = f"{file_cnt:03d}"

            bg_only_wav = False

            if 'scriptData' in upload:
                if upload['scriptData'] != "":
                    script_data = upload['scriptData'][1:-1].split('content:')[1]
                    if script_data == 'DO NOT RECORD THIS TEXT. Record ONLY the background noise for 1min to 1.5min.':
                        bg_only_wav = True

            if bg_only_wav:
                wav_file_path = folder_name + speaker_id_str + '-' + '000-1' + '.wav'
                json_file_path = folder_name + speaker_id_str + '-' + '000-1' + '.json'
                if os.path.isfile(wav_file_path):
                    wav_file_path = folder_name + speaker_id_str + '-' + '000-2' + '.wav'
                    json_file_path = folder_name + speaker_id_str + '-' + '000-2' + '.json'
            else:
                wav_file_path = folder_name + speaker_id_str + '-' + file_cnt_str + '.wav'
                json_file_path = folder_name + speaker_id_str + '-' + file_cnt_str + '.json'

            if dry_run:
                create_empty_file(wav_file_path)
            else:
                if file_already_present(wav_file_path, upload_md5):
                    print('File already downloaded, avoiding re-download.')
                else:
                    if not download_file(upload_url, wav_file_path):
                        download_error = True
                    else:
                        if(is_zip_file(wav_file_path)):
                            unzip_file(wav_file_path)

                        if(is_flac_file(wav_file_path)):
                            convert_flac_to_wav(wav_file_path)

            gender = None
            age = None

            if consent_form_enabled:
                if object_rejected:
                    output_path = project_prefix + reject_prefix + task_name + '/'
                elif object_pending:
                    output_path = project_prefix + pending_prefix + task_name + '/'
                else:
                    output_path = project_prefix + approve_prefix + task_name + '/'

                consent_form_data = upload['consentFormData']

                gender = get_value_by_name(consent_form_data, 'CF_Gender') #consent_form_data[3]['value']
                age = get_value_by_name(consent_form_data, 'CF_Age') #consent_form_data[2]['value']

                #generate_consent_form(consent_form_data, project_name, task_name, output_path, idx)

                if not save_individual_recordings:
                    consent_form_saved = True

            if gender == None or age == None:
                print('Gender or Age is None.. ', gender, age)
                exit()

            metadata_data[speaker_id_str]['Age'] = age
            metadata_data[speaker_id_str]['Gender'] = gender
            metadata_data[speaker_id_str]['Recording Device'] = 'Mobile'

            acoustic_environment = None

            if 'scriptData' in upload:
                if upload['scriptData'] != "":
                    script_file = wav_file_path.split('.')[0]+'_script.txt'
                    script_data = upload['scriptData'][1:-1].split('content:')[1]
                    script_topic_id = script_map[script_data]
                    if not bg_only_wav:
                        script_topic = conversation_categories[script_topic_id] if script_topic_id in conversation_categories else conversation_categories_remapped[script_topic_id] 
                    metadata_json = {
                            "text": '' if bg_only_wav else script_data,
                            "topic": '' if bg_only_wav else script_topic,
                            "acoustic_environment": acoustic_environments_map[str(upload_id)],
                            "recording_device": "Mobile",
                            "speaker_name": speaker_id_str,
                            "gender": '' if bg_only_wav else gender,
                            "language": '' if bg_only_wav else language,
                            "native_language": '' if bg_only_wav else language,
                            "accent": '' if bg_only_wav else language
                        }

                    acoustic_environment = acoustic_environments_map[str(upload_id)]

                    with open(json_file_path, 'w') as file:
                        json.dump(metadata_json, file, indent=4, ensure_ascii=False)  # indent for pretty formatting

            if 'Acoustic Environment 1' not in metadata_data[speaker_id_str]:
                metadata_data[speaker_id_str]['Acoustic Environment 1'] = acoustic_environment
            else:
                metadata_data[speaker_id_str]['Acoustic Environment 2'] = acoustic_environment

        if not task_skipped:
            new_users_from_this_release[user_id] = [upload['userName'], speaker_id_str, user_upload_approval_count[user_id]]

    speaker_map_csv = speaker_map_csv | new_users_from_this_release

    if not dry_run:
        speaker_map_json_to_csv(speaker_map_csv, db_file_name)

    # Get current date
    current_date = datetime.now()

    # Format as day_MonthAbbr_Year
    formatted_date = current_date.strftime("%d_%b_%Y")

    if metadata_folder:
        metadata_file = metadata_folder + '/Metadata_'+ formatted_date + '.csv'

        create_csv_from_nested_dict(metadata_data, metadata_header, metadata_file)

        print('Created Metadata file - ', metadata_file)
    else:
        print('No metadata')

    if download_error:
        print('\nDownload Error - Probably the pre-signed urls expired. Please try downloading the Download Config File again or contact AIDAC support if issue persists.')
    else:
        print('\nDownload Successful - Dataset downloaded under \'aidac\' folder.')

if __name__ == "__main__":
    main()
