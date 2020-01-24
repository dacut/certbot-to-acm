# certbot-to-acm
Connect Certbot to Amazon Certificate Manager via Lambda

## Certbot-to-ACM ZIP file
A Lambda-deployable ZIP file containing the function code is available in each
region: <tt>s3://ionosphere-public-<i>region</i>/certbot-to-acm.zip</tt>

This ZIP file depends on the Certbot layer below.

## Certbot Lambda layer
The Certbot Lambda layer is available for download in each region. There is a
separate version for each supported Python version:

* Python 3.6: <tt>s3://ionosphere-public-<i>region</i>/certbot-layer-py3.6.zip</tt>
* Python 3.7: <tt>s3://ionosphere-public-<i>region</i>/certbot-layer-py3.7.zip</tt>
* Python 3.8: <tt>s3://ionosphere-public-<i>region</i>/certbot-layer-py3.8.zip</tt>

The Lambda layer can also be ingested directly into your function. The current
layer ARNs are:
<table style="font-size: 75%;">
  <tr><td rowspan='3'>ap-east-1</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-east-1:966028770618:layer:certbot-py36:2</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-east-1:966028770618:layer:certbot-py37:2</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-east-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ap-northeast-1</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-northeast-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-northeast-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-northeast-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ap-northeast-2</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-northeast-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-northeast-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-northeast-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ap-south-1</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-south-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-south-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-south-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ap-southeast-1</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-southeast-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-southeast-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-southeast-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ap-southeast-2</td><td>python3.6</td><td><tt>arn:aws:lambda:ap-southeast-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ap-southeast-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ap-southeast-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>ca-central-1</td><td>python3.6</td><td><tt>arn:aws:lambda:ca-central-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:ca-central-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:ca-central-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>eu-central-1</td><td>python3.6</td><td><tt>arn:aws:lambda:eu-central-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:eu-central-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:eu-central-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>eu-north-1</td><td>python3.6</td><td><tt>arn:aws:lambda:eu-north-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:eu-north-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:eu-north-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>eu-west-1</td><td>python3.6</td><td><tt>arn:aws:lambda:eu-west-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:eu-west-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:eu-west-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>eu-west-2</td><td>python3.6</td><td><tt>arn:aws:lambda:eu-west-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:eu-west-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:eu-west-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>eu-west-3</td><td>python3.6</td><td><tt>arn:aws:lambda:eu-west-3:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:eu-west-3:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:eu-west-3:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>me-south-1</td><td>python3.6</td><td><tt>arn:aws:lambda:me-south-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:me-south-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:me-south-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>sa-east-1</td><td>python3.6</td><td><tt>arn:aws:lambda:sa-east-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:sa-east-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:sa-east-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-east-1</td><td>python3.6</td><td><tt>arn:aws:lambda:us-east-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:us-east-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:us-east-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-east-2</td><td>python3.6</td><td><tt>arn:aws:lambda:us-east-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:us-east-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:us-east-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-west-1</td><td>python3.6</td><td><tt>arn:aws:lambda:us-west-1:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:us-west-1:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:us-west-1:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-west-2</td><td>python3.6</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-west-2</td><td>python3.6</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws:lambda:us-west-2:966028770618:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-gov-east-1</td><td>python3.6</td><td><tt>arn:aws-us-gov:lambda:us-gov-east-1:678832456889:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws-us-gov:lambda:us-gov-east-1:678832456889:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws-us-gov:lambda:us-gov-east-1:678832456889:layer:certbot-py38:1</tt></td></tr>
  <tr><td rowspan='3'>us-gov-west-1</td><td>python3.6</td><td><tt>arn:aws-us-gov:lambda:us-gov-west-1:678832456889:layer:certbot-py36:1</tt></td></tr>
  <tr><td>python3.7</td><td><tt>arn:aws-us-gov:lambda:us-gov-west-1:678832456889:layer:certbot-py37:1</tt></td></tr>
  <tr><td>python3.8</td><td><tt>arn:aws-us-gov:lambda:us-gov-west-1:678832456889:layer:certbot-py38:1</tt></td></tr>
</table>
