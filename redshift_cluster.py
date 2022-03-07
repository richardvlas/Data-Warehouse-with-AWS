import os
import sys
import time
import json
import argparse
import logging
import configparser
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
logger = logging.getLogger()

# Load and parse DWH Params from a configuration file
config = configparser.ConfigParser()
config.read_file(open('dwh.cfg'))

KEY                    = config.get('AWS', 'KEY')
SECRET                 = config.get('AWS', 'SECRET')

DWH_CLUSTER_TYPE       = config.get("CLUSTER", "DWH_CLUSTER_TYPE")
DWH_NUM_NODES          = config.get("CLUSTER", "DWH_NUM_NODES")
DWH_NODE_TYPE          = config.get("CLUSTER", "DWH_NODE_TYPE")
DWH_CLUSTER_IDENTIFIER = config.get("CLUSTER", "DWH_CLUSTER_IDENTIFIER")

DWH_DB_NAME            = config.get("DB", "DWH_DB_NAME")
DWH_DB_USER            = config.get("DB", "DWH_DB_USER")
DWH_DB_PASSWORD        = config.get("DB", "DWH_DB_PASSWORD")
DWH_PORT               = config.get("DB", "DWH_DB_PORT")

DWH_IAM_ROLE_NAME      = config.get("IAM_ROLE", "DWH_IAM_ROLE_NAME")

S3_READ_ARN = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"


def create_resource_service_clients():
    """
    Create a resource service clients by name
    
    Returns:
    --------
    ec2 : e2.ServiceResource
        e2 service client
    
    s3 : s3.ServiceResource
        s3 service client

    iam : botocore.client.IAM
        iam service client
    
    redshift: botocore.client.Redshift
        redshift service client
    """
    client_options = {
        'region_name': "us-west-2",
        'aws_access_key_id': KEY,
        'aws_secret_access_key': SECRET
    }

    ec2 = boto3.resource('ec2', **client_options)

    s3 = boto3.resource('s3', **client_options)

    iam = boto3.client('iam', **client_options)

    redshift = boto3.client('redshift', **client_options)

    return ec2, s3, iam, redshift


def create_iam_role(iam):
    """
    Creates a new role for your Amazon Web Services account

    Parameters:
    -----------
    iam : botocore.client.IAM
        iam service client

    Returns:
    --------
    role_arn : str
        Amazon iam's Resource Name (ARN)
    """
    try:
        logger.info("Creating a new IAM Role...") 
        dwhRole = iam.create_role(
            Path='/',
            RoleName=DWH_IAM_ROLE_NAME,
            Description = "Allows Redshift clusters to call AWS services on your behalf.",
            AssumeRolePolicyDocument=json.dumps(
                {'Statement': [{'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {'Service': 'redshift.amazonaws.com'}}],
                'Version': '2012-10-17'})
        )    
    except ClientError as e:
        logger.error(e)
        
    try:
        logger.info("Attaching Policy...") 
        iam.attach_role_policy(RoleName=DWH_IAM_ROLE_NAME,
                               PolicyArn=S3_READ_ARN
                              )
    except ClientError as e:
        logger.error(e)
        
    role_arn = iam.get_role(RoleName=DWH_IAM_ROLE_NAME)['Role']['Arn']
    logger.info(f"Created role: {DWH_IAM_ROLE_NAME} with Amazon Resource Name (ARN): {role_arn}")

    return role_arn


def create_redshift_cluster(redshift, role_arn):
    """
    Create a new Readshift cluster

    Parameters:
    -----------
    redshift: botocore.client.Redshift
        redshift service client

    role_arn : str
        Amazon iam's Resource Name (ARN)
    """
    try:
        logger.info("Creating a Redshift cluster...")
        redshift.create_cluster(
            # HW
            ClusterType=DWH_CLUSTER_TYPE,
            NodeType=DWH_NODE_TYPE,
            NumberOfNodes=int(DWH_NUM_NODES),
            
            # Identifiers & Credentials
            DBName=DWH_DB_NAME,
            ClusterIdentifier=DWH_CLUSTER_IDENTIFIER,
            MasterUsername=DWH_DB_USER,
            MasterUserPassword=DWH_DB_PASSWORD,
            
            # Roles (for s3 access)
            IamRoles=[role_arn],
        )
    except ClientError as e:
        logger.error(e)


def open_tcp_port(ec2, vpc_id):
    """
    Open a TCP port connection to access the cluster endpoint
    
    Parameters:
    -----------
    vpc_id : str
        The Vpc's id identifier
    """
    try:
        vpc = ec2.Vpc(id=vpc_id)
        defaultSg = list(vpc.security_groups.all())[0]
        
        defaultSg.authorize_ingress(
            GroupName=defaultSg.group_name,
            CidrIp='0.0.0.0/0',
            IpProtocol='TCP',
            FromPort=int(DWH_PORT),
            ToPort=int(DWH_PORT)
        )
    except ClientError as e:
        logger.error(e)


def delete_iam_role(iam):
    """
    Delete an existing role for your Amazon Web Services account

    Parameters:
    -----------
    iam : botocore.client.IAM
        iam service client
    """
    try:
        role_arn = iam.get_role(RoleName=DWH_IAM_ROLE_NAME)['Role']['Arn']
        iam.detach_role_policy(RoleName=DWH_IAM_ROLE_NAME, PolicyArn=S3_READ_ARN)
        iam.delete_role(RoleName=DWH_IAM_ROLE_NAME)

        logger.info(f"Deleted role: {DWH_IAM_ROLE_NAME} with Amazon Resource Name (ARN): {role_arn}")
    
    except ClientError as e:
        logger.error(e)
    
    
def delete_redshift_cluster(redshift):
    """
    Delete an existing Readshift cluster

    Parameters:
    -----------
    redshift: botocore.client.Redshift
        redshift service client
    """
    try:
        redshift.delete_cluster(
            ClusterIdentifier=DWH_CLUSTER_IDENTIFIER,
            SkipFinalClusterSnapshot=True
        )
        logger.info(f'Cluster {DWH_CLUSTER_IDENTIFIER} deleted!')

    except ClientError as e:
        logger.error(e)


def main(args):
    """
    Main script to create and configure the resources
    """
    logger.info("Creating a resource service clients...")
    ec2, s3, iam, redshift = create_resource_service_clients()

    if args.action == 'create':        
        role_arn = create_iam_role(iam)
        create_redshift_cluster(redshift, role_arn)

        # Check and loop until the Redshift cluster status becomes Available
        myClusterProps = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
        while myClusterProps['ClusterStatus'] != 'available':
            myClusterProps = redshift.describe_clusters(
                ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
            
            # Show waiting dots
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)

        logger.info(f"Cluster status: {myClusterProps['ClusterStatus']}")

        DWH_ENDPOINT = myClusterProps['Endpoint']['Address']
        DWH_ROLE_ARN = myClusterProps['IamRoles'][0]['IamRoleArn']

        logger.info(f"Logging DWH enpoint: {DWH_ENDPOINT}")
        logger.info(f"Logging DWH role ARN: {DWH_ROLE_ARN}")

        logger.info("Opening a TCP port connection...")
        open_tcp_port(ec2, myClusterProps['VpcId'])


    if args.action == 'delete':
        delete_redshift_cluster(redshift)
        delete_iam_role(iam)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create and configure the DWH resources on AWS")

    parser.add_argument('action', 
                        type=str, 
                        choices=["create", "delete"], 
                        help="create a new cluster or delete an existing one"
                        )

    args = parser.parse_args()

    main(args)
