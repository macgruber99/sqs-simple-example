# Third-party library imports
import boto3

sqs = boto3.client('sqs')
# ssm = boto3.client('ssm')
# ssm_param_name = "/sqs-simple-example/queue-url"

# def get_ssm_parameter(param_name):
#     """
#     Fetches a parameter value from AWS SSM Parameter Store.

#     :param parameter_name: The name of the parameter to fetch.
#     :return: The value of the parameter.
#     """
#     try:
#         response = ssm.get_parameter(
#             Name=param_name,
#         )
#         return response['Parameter']['Value']
#     except Exception as e:
#         print(f"Error fetching parameter {param_name}: {e}")
#         raise


def lambda_handler(event, context):
    """
    AWS Lambda handler function to send a message to SQS.
    
    :param event: The event data passed to the Lambda function.
    :param context: The runtime information of the Lambda function.
    """

    print(event)
    print(context)
