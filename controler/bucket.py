import configparser

import boto3

config = configparser.ConfigParser()
config.read('etc/config.ini')

class Bucket:
    def __init__(self):
        self.region_name = config.get('aws', 'region_name')
        self.access_key = config.get('aws', 'access_key')
        self.secret_access_key = config.get('aws', 'secret_access_key')
        self.bucket_name = config.get('aws', 'bucket_name_prev')

        self.s3 = boto3.client(
            's3',
            region_name=self.region_name, 
            aws_access_key_id = self.access_key, 
            aws_secret_access_key= self.secret_access_key    
        )
    
    def upload(self, filename, key):
        try:
            self.s3.upload_file(
                Filename=filename,
                Bucket=self.bucket_name,
                Key=key
            )
        except Exception as e:
            print(f"[controller.Bucket.upload] {str(e)}")