#!/bin/bash

# --- Configuration ---
BUCKET_NAME="myawsbucket9660551704"
AWS_REGION="ap-south-1"  # Change if needed

# --- Step 1: Count existing .txt files in the S3 bucket ---
echo "Counting existing .txt files in bucket..."
count=$(aws s3 ls s3://$BUCKET_NAME/ --region $AWS_REGION | grep -E '\.txt$' | wc -l)
new_version=$((count + 1))
new_filename="release_${new_version}.txt"

# --- Step 2: Create a version file ---
echo "Creating $new_filename locally..."
cat version.txt > "$new_filename"

# --- Step 3: Upload to S3 ---
echo "Uploading $new_filename to s3://$BUCKET_NAME/ ..."
aws s3 cp "$new_filename" s3://$BUCKET_NAME/ --region $AWS_REGION

# --- Step 4: Clean up ---
rm "$new_filename"
echo "Done. Uploaded $new_filename to S3."
