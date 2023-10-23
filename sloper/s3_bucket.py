import boto3
from django.conf import settings


class BucketFiles:
    __s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    __bucket = __s3.Bucket('megadolls-devteam')
    
    def __init__(self, file_path):
        self.file_path = file_path

    '''
        Create file and write data in the file which stored on s3 bucket
    '''
    def save(self, data=None):
        # try:
            buck = self.__bucket.Object(self.file_path)
            if isinstance(data, bytes):
                converted_to_byte_data = data
            else:
                converted_to_byte_data = data.encode('ascii')
            res = buck.put(Body=converted_to_byte_data)
            response = res.get('ResponseMetadata')
            return response.get('HTTPStatusCode') == 200
        # except:
        #     return False

    '''
        Get Data from the file in string bytes
    '''
    def get_file_data(self):
        # try:
            buck = self.__bucket.Object(self.file_path).get()
            return buck['Body'].read()
        # except:
        #     return None