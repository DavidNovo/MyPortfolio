import json
import boto3
import io
import zipfile
import mimetypes


def lambda_handler(event, context):
    # set up alerts
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-2:233902555877:deployPortfolioTopic')

    try:
        # default location, allows lambda to run outside CodePipeline
        location = {
            "bucketName": 'portfoliobuild.novogrodsky.net',
            "objectKey": 'portfolioBuild.zip'
        }
        # get the event object from CodePipeline
        job = event.get("CodePipeline.job")
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "BuildArtifact":
                    location = artifact["location"]["s3Location"]
        print("Build portfolio from " + str(location)) 

        # first get the files in the build bucket
        # CodeBuild deploys files with server-side encryption
        from botocore.client import Config
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
        
        portfolio_bucket = s3.Bucket('portfolio.novogrodsky.net')
        build_bucket = s3.Bucket(location["bucketName"])
        
        # download the zip file file
        # not to bucket but in-memory container
        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)
        # the destination is a BytesIO object
        
        # expand the zip file
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                # upload the files to the deploy bucket, setting the mime type
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
                # set the axccess on the deploy bucket as public
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
            
        topic.publish(Subject="Portfolio Deployed", Message='Portfolio deployed successfully')
        # notify CodePipeline lambda is done
        if job:
            codePipeline = boto3.client('codepipeline')
            codePipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="Portfolio Not Deployed", Message='Portfolio not deployed successfully')
        raise
    return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }