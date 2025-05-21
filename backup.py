import os
import shutil
import logging
import subprocess
import pickle
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def get_google_drive_credentials(token_filename='token.pickle', credentials_file='credentials.json'):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None

    if os.path.exists(token_filename):
        with open(token_filename, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_filename, 'wb') as token:
            pickle.dump(creds, token)

    return creds


class BackupManager:

    def __init__(self, source_folder, backup_folder, log_file="backup.log"):
        self.source_folder = source_folder
        self.backup_folder = backup_folder
        self.log_file = log_file
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.backup_name = f"backup_{self.timestamp}.zip"
        self.backup_path = os.path.join(self.backup_folder, self.backup_name)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def run_backup(self):
        logging.info("Backup started.")
        try:
            os.makedirs(self.backup_folder, exist_ok=True)
            shutil.make_archive(self.backup_path.replace(".zip", ""), "zip", self.source_folder)
            logging.info(f"Backup successful: {self.backup_path}")
            print(f"✅ Backup created at: {self.backup_path}")
        except Exception as e:
            logging.error(f"❌ Backup failed: {str(e)}")
            print(f"❌ Error during backup: {str(e)}")

    def upload_scp(self, remote_path):
        try:
            result = subprocess.run(["scp", self.backup_path, remote_path])
            if result.returncode == 0:
                logging.info("✅ SCP upload successful.")
                print("✅ SCP upload successful.")
            else:
                logging.error("❌ SCP upload failed.")
                print("❌ SCP upload failed.")
        except Exception as e:
            logging.error(f"SCP Exception: {e}")
            print(f"SCP Exception: {e}")

    def upload_to_drive(self):
        creds = get_google_drive_credentials()

        try:
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {'name': os.path.basename(self.backup_path)}
            media = MediaFileUpload(self.backup_path, mimetype='application/zip')
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get("id")
            link = f"https://drive.google.com/file/d/{file_id}/view"
            print(f"✅ Uploaded to Google Drive: {link}")
            logging.info(f"Uploaded to Google Drive: {link}")

        except Exception as e:
            logging.error(f"❌ Google Drive upload failed: {e}")
            print(f"❌ Google Drive upload failed: {e}")


if __name__ == "__main__":
    manager = BackupManager("folders/my_project", "backups")
    manager.run_backup()
    manager.upload_to_drive()

