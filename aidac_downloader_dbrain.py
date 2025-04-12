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

conversation_categories = {
    "1": "Social Interaction and Communication",
    "2": "Entertainment and Leisure",
    "3": "Education and Learning",
    "4": "Working Place Cooperation", 
    "5": "Health and Wellness",
    "6": "Travel and Navigation",
    "7": "Finance and Budgeting",
    "8": "Home Management",
    "9": "Content Creation and Creative Arts",
    "10": "Customer Support",
    "11": "Customer Support",
    "12": "Accessibility",
    "13": "Legal and Ethical Guidance",
    "14": "Miscellaneous",
    "15": "Special Types of Conversations"
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

def is_object_pending (uploads):

    pending_list = [
        upload for upload in uploads
        if upload['approvalStatus'] == 2
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

def main():
    parser = argparse.ArgumentParser(description="AIDAC Downloader - Download dataset directly from cloud storage.")
    
    # Add command line arguments
    parser.add_argument("-c", "--download-cfg", type=str, help="Download Config File (JSON)", required=True)
    parser.add_argument("-i", "--ignore-rejected", action='store_true', help="Ignore and do not download rejected datasets")
    parser.add_argument("-s", "--script-csv", type=str, help="Script CSV", required=True)
    parser.add_argument("-l", "--language", type=str, help="Language", required=True)
    parser.add_argument("-m", "--metadata-csv", type=str, help="Metaata CSV", required=True)

    args = vars(parser.parse_args())

    download_cfg_file = args['download_cfg']
    ignore_rejected = args['ignore_rejected']
    csv_filename =  args['script_csv']
    language =  args['language']
    metadata_csv = args['metadata_csv']

    if not os.path.isfile(download_cfg_file):
        print('Error: ', download_cfg_file, 'file not found')
        exit()

    download_data = None
    # Load json data from file
    with open(download_cfg_file, 'r') as f:
        download_data = json.load(f)

    # Example usage:
    script_map = csv_to_dict(csv_filename)

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

    project_prefix = 'aidac/'+project_name+'/'
    approve_prefix = 'qc_approved/'
    reject_prefix = 'qc_rejected/'
    pending_prefix = 'qc_pending/'

    print('\n******************************************************************')
    print(' AIDAC Downloader - Downloads dataset and generates consent forms')
    print('******************************************************************\n')
 
    download_error = False

    speaker_id = 1

    user_id_map = {}
    current_user_id = None
    metadata_header = ['ID', 'Mobile Number', 'Language', 'Native Language', 'Accent', 'Age', 'Gender', 'Recording Device', 'Acoustic Environment 1', 'Acoustic Environment 2']
    metadata_data = {}
    metadata_folder = None

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

        if ignore_rejected and object_rejected:
            continue

        for idx, upload in enumerate(obj_uploads):
            upload_id = upload['id']
            upload_file_name = upload['fileName']
            upload_url = upload['s3Url']
            upload_md5 = upload['md5']
            upload_approval_status = upload['approvalStatus']
            user_id = upload['userId']

            if user_id != current_user_id:
                if user_id not in user_id_map:
                    formatted_speaker_id = f"{speaker_id:04d}"  
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
            file_cnt_str = f"{file_cnt:04d}"

            wav_file_path = folder_name + speaker_id_str + '-' + file_cnt_str + '.wav'
            json_file_path = folder_name + speaker_id_str + '-' + file_cnt_str + '.json'

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

                gender = consent_form_data[3]['value']
                age = consent_form_data[2]['value']

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
                    script_topic = conversation_categories[script_topic_id]
                    metadata_json = {
                            "text": script_data,
                            "topic": script_topic,
                            "acoustic_environment": acoustic_environments_map[str(upload_id)],
                            "recording_device": "Mobile",
                            "speaker_name": speaker_id_str,
                            "gender": gender,
                            "language": language,
                            "native_language": language,
                            "accent": language
                        }

                    acoustic_environment = acoustic_environments_map[str(upload_id)]

                    with open(json_file_path, 'w') as file:
                        json.dump(metadata_json, file, indent=4, ensure_ascii=False)  # indent for pretty formatting
            

            if 'Acoustic Environment 1' not in metadata_data[speaker_id_str]:
                metadata_data[speaker_id_str]['Acoustic Environment 1'] = acoustic_environment
            else:
                metadata_data[speaker_id_str]['Acoustic Environment 2'] = acoustic_environment


    # Get current date
    current_date = datetime.now()

    # Format as day_MonthAbbr_Year
    formatted_date = current_date.strftime("%d_%b_%Y")

    metadata_file = metadata_folder + '/Metadata_'+ formatted_date + '.csv'

    create_csv_from_nested_dict(metadata_data, metadata_header, metadata_file)

    print('Created Metadata file - ', metadata_file)

    if download_error:
        print('\nDownload Error - Probably the pre-signed urls expired. Please try downloading the Download Config File again or contact AIDAC support if issue persists.')
    else:
        print('\nDownload Successful - Dataset downloaded under \'aidac\' folder.')

if __name__ == "__main__":
    main()
