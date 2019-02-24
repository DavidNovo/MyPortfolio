import boto3
import io
import zipfile
import mimetypes

# first get the files in the build bucket
# CodeBuild deploys files with server-side encryption
from botocore.client import Config
s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

portfolio_bucket = s3.Bucket('portfolio.novogrodsky.net')
build_bucket = s3.Bucket('portfoliobuild.novogrodsky.net')

# download the zip file file
# not to bucket but in-memory container
portfolio_zip = io.BytesIO()
build_bucket.download_fileobj('portfolioBuild.zip', portfolio_zip)
# the destination is a BytesIO object

# expand the zip file
with zipfile.ZipFile(portfolio_zip) as myzip:
    for nm in myzip.namelist():
        obj = myzip.open(nm)
        # upload the files to the deploy bucket, setting the mime type
        portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
        # set the axccess on the deploy bucket as public
        portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
