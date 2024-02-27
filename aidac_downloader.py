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

def generate_consent_form(consent_form_json, project_name):
    
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

    with open(consent_form_json, 'r') as f:
        consent_form_data = json.load(f)

    x_pos = 100
    y_pos += 100
    y_off = 80

    text = "Project Name : " + project_name
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "First Name : " + consent_form_data['firstName']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Last Name : " + consent_form_data['lastName']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Email : " + consent_form_data['email']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Age : " + consent_form_data['age']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Ethnicity : " + consent_form_data['ethnicity']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Country of Origin : " + consent_form_data['selectedCountryOfOrigin']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Country of Residence : " + consent_form_data['selectedResidingCountry']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off
    text = "Gender : " + consent_form_data['gender']
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    if 'skinTone' in consent_form_data.keys():
        y_pos += y_off
        text = "Skin Tone : " + consent_form_data['skinTone']
        cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    y_pos += y_off + 50
    text = "Signature : " 
    cv2.putText(img, text, (x_pos, y_pos), font, 1, (0, 0, 0), 1, cv2.LINE_AA)

    signature_b64 = consent_form_data['signature']
    signature_png = convert_b64_to_png(signature_b64)

    signature_png = cv2.resize(signature_png, (0, 0), fx = 0.2, fy = 0.2)

    trans_mask = signature_png[:,:,3] == 0
    signature_png[trans_mask] = [255, 255, 255, 255]
    signature_png = cv2.cvtColor(signature_png, cv2.COLOR_BGRA2BGR)

    x_pos = 350
    y_pos -= 80
    sign_height, sign_width, _ = signature_png.shape

    img[y_pos:y_pos+sign_height, x_pos:x_pos+sign_width] = signature_png

    file_name_base, _ = os.path.splitext(consent_form_json)

    jpg_file_name = file_name_base + '.jpg'

    cv2.imwrite(jpg_file_name, img)

    pdf_file_name = file_name_base + '.pdf'

    with open(pdf_file_name,"wb") as f:
        f.write(img2pdf.convert(jpg_file_name))

    os.remove(jpg_file_name)
    os.remove(consent_form_json)


def main():
    parser = argparse.ArgumentParser(description="AIDAC Downloader - Download dataset directly from cloud storage.")
    
    # Add command line arguments
    parser.add_argument("-c", "--download-cfg", type=str, help="Download Config File (JSON)", required=True)
    parser.add_argument("-i", "--ignore-rejected", action='store_true', help="Ignore and do not download rejected datasets")

    args = vars(parser.parse_args())

    download_cfg_file = args['download_cfg']
    ignore_rejected = args['ignore_rejected']

    if not os.path.isfile(download_cfg_file):
        print('Error: ', download_cfg_file, 'file not found')
        exit()

    # Load json data from file
    with open(download_cfg_file, 'r') as f:
        download_data = json.load(f)

    project_id = download_data['id']
    project_name = download_data['name']
    is_grouping = download_data['groupingProject']

    consent_form_enabled = False
    if 'consentFormStatus' in download_data.keys():
        consent_form_enabled = True if download_data['consentFormStatus'] else False

    objects = download_data['objects']

    project_prefix = 'aidac/'+project_name+'/'
    approve_prefix = 'qc_approved/'
    reject_prefix = 'qc_rejected/'
    pending_prefix = 'qc_pending/'

    print('\n******************************************************************')
    print(' AIDAC Downloader - Downloads dataset and generates consent forms')
    print('******************************************************************\n')
 
    download_error = False

    for obj in objects:
        obj_id = obj['id']
        obj_name = obj['name']
        obj_uploads = obj['uploads']
        if consent_form_enabled:
            obj_consent_form_url = obj['consentFormUrl']

        object_rejected = False        
        object_pending = False        
        if is_grouping:
            object_rejected = is_object_rejected(obj_uploads)
            object_pending = is_object_pending(obj_uploads)

        if ignore_rejected and object_rejected:
            continue

        for upload in obj_uploads:
            upload_id = upload['id']
            upload_file_name = upload['fileName']
            upload_url = upload['s3Url']
            upload_md5 = upload['md5']
            upload_approval_status = upload['approvalStatus']

            if object_rejected:
                folder_name = project_prefix + reject_prefix
            elif object_pending:
                folder_name = project_prefix + pending_prefix
            else:
                folder_name = project_prefix + approve_prefix

            folder_name += obj_name + '/'

            create_folder(folder_name)

            file_path = folder_name + upload_file_name

            if file_already_present(file_path, upload_md5):
                print('File already downloaded, avoiding re-download.')
            else:
                if not download_file(upload_url, file_path):
                    download_error = True

            if 'scriptData' in upload:
                if upload['scriptData'] != "":
                    script_file = file_path.split('.')[0]+'_script.txt'
                    script_data = upload['scriptData'][1:-1].split('content:')[1]
                    print('saving script file to - ', script_file)
                    with open(script_file, 'w') as f:
                        f.write(script_data)

        if consent_form_enabled:
            if object_rejected:
                folder_name = project_prefix + reject_prefix + obj_name + '/'
            elif object_pending:
                folder_name = project_prefix + pending_prefix + obj_name + '/'
            else:
                folder_name = project_prefix + approve_prefix + obj_name + '/'

            file_path = folder_name + obj_name + '_consent_form.json'
            if obj_consent_form_url != None:
                if download_file(obj_consent_form_url, file_path):
                    generate_consent_form(file_path, project_name)
                else:
                    download_error = True
            

    if download_error:
        print('\nDownload Error - Probably the pre-signed urls expired. Please try downloading the Download Config File again or contact AIDAC support if issue persists.')
    else:
        print('\nDownload Successful - Dataset downloaded under \'aidac\' folder.')

if __name__ == "__main__":
    main()
