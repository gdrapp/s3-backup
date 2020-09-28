# s3-backup.py 
Backup local files to Amazon S3. Files are bundled into a tar.gz file before they are uploaded.

## Installation
```
git clone https://github.com/gdrapp/s3-backup
pip3 install -r requirements.txt
```

## Configuration
Configuration is YAML based and is located in config.yaml.

Example configuration:
```
tarfile_name_prefix: "server_"
sources:
    - /etc
exclusions:
    - '.*\.log$'
s3:
    bucket_region: us-west-1
    bucket_name: my-backups
    storage_class: STANDARD
```
### Option: `tarfile_name_prefix`
Prefix to prepend to backup file name.

### Option: `sources` (required)
Location to include in the backup.

### Option: `exclusions`
Do not backup files or directories that match these regular expressions.

### Option: `s3.bucket_region` (required)
AWS region containing the S3 bucket where backup file will be copied.

### Option: `s3.bucket_name` (required)
Name of the S3 bucket where backup file will be copied

### Option: `s3.storage_class` (required)
Amazon S3 storage class to use when storing the backup file in S3.