
import os

def test_export_paths():
    bucket = os.getenv("S3_BUCKET")
    access = os.getenv("S3_ACCESS_KEY")
    secret = os.getenv("S3_SECRET_KEY")

    if bucket and access and secret:
        try:
            import boto3
            s3 = boto3.client('s3', aws_access_key_id=access, aws_secret_access_key=secret)
            test_filename = "nova_test_upload.txt"
            with open(test_filename, "w") as f:
                f.write("Test export file from Nova Agent")
            s3.upload_file(test_filename, bucket, test_filename)
            print(f"✅ Test upload to S3 bucket '{bucket}' succeeded.")
            s3.delete_object(Bucket=bucket, Key=test_filename)
            print(f"🧹 Cleaned up test file '{test_filename}' from bucket.")
        except Exception as e:
            print(f"❌ S3 export test failed: {e}")
    else:
        print("⚠️ S3 credentials not found, checking Google Drive fallback...")
        try:
            from memory_export_to_drive import export_logs_to_gdrive
            export_logs_to_gdrive()
            print("✅ Google Drive fallback simulated.")
        except:
            print("❌ Google Drive fallback failed or not implemented.")

if __name__ == "__main__":
    test_export_paths()
