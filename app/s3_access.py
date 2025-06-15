import boto3

s3 = boto3.client('s3')

bucket_name = 'romitestbucket07'
prefix = 'llm-dev/security_data/'

# Filter criteria
filter_tags = {
    'model_config': 'test1',
    'user_id': 'rajarshi.maity@infosys.com'
}

# Initialize boto3 client
s3 = boto3.client('s3')

# Paginate through files under the prefix
paginator = s3.get_paginator('list_objects_v2')
page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

for page in page_iterator:
    for obj in page.get('Contents', []):
        key = obj['Key']
        
        # Skip if it's a folder marker
        if key.endswith('/'):
            continue

        # Fetch tags
        tagging = s3.get_object_tagging(Bucket=bucket_name, Key=key)
        tags = {tag['Key']: tag['Value'] for tag in tagging['TagSet']}

        # Match tags
        if all(tags.get(k) == v for k, v in filter_tags.items()):
            print(f"Matched file: s3://{bucket_name}/{key}")
            
            # Fetch and decode file contents
            response = s3.get_object(Bucket=bucket_name, Key=key)
            response_content = response['Body'].read().decode('utf-8')
            
            print("Contents:\n", response_content)
