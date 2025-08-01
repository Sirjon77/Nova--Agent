
import boto3
import os

def export_logs_to_s3(bucket_name, access_key, secret_key):
    s3 = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)

    files_to_export = ["prompt_lineage.json", "ab_test_log.json", "loop_health_report.json"]
    for file in files_to_export:
        if os.path.exists(file):
            s3.upload_file(file, bucket_name, file)
            print(f"Uploaded {file} to S3 bucket {bucket_name}")

if __name__ == "__main__":
    export_logs_to_s3(
        bucket_name=os.getenv("S3_BUCKET"),
        access_key=os.getenv("S3_ACCESS_KEY"),
        secret_key=os.getenv("S3_SECRET_KEY")
    )
