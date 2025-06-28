# Python Standard Library imports
import argparse
import json

from datetime import datetime
from datetime import timezone

# Third-party library imports
import boto3
import lorem


def write_obj_to_s3(bucket_name, file_name, content):
    """
    Writes content to a file in an S3 bucket.

    :param bucket_name: The name of the S3 bucket.
    :param file_name: The name of the file to create in the bucket.
    :param content: The content to write to the file.
    :return: A dictionary with response data.
    """

    client = boto3.client("s3")
    client.put_object(Bucket=bucket_name, Key=file_name, Body=content)


def main():
    """
    Main function to write a message to an S3 bucket.
    """

    # define some variables
    sentence = lorem.sentence()  # generate random text that looks like Latin
    timestamp = datetime.now(timezone.utc).isoformat()
    first_word = sentence.split()[0]  # get the first word of the sentence
    s3_obj_key = f"{first_word}-{timestamp}.json"  # create a unique file name based on the timestamp

    message = {"text": sentence, "timestamp": timestamp}

    # parse the command line arguments
    parser = argparse.ArgumentParser(description="Write a message to an S3 bucket.")
    parser.add_argument("bucket_name", type=str, help="The name of the S3 bucket")
    args = parser.parse_args()

    # write the message to S3
    write_obj_to_s3(args.bucket_name, s3_obj_key, json.dumps(message))


if __name__ == "__main__":
    main()
