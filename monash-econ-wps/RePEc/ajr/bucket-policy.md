```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::509336869814:role/cognito_monash_econ_wps_role"
            },
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::monash-econ-wps"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::509336869814:role/cognito_monash_econ_wps_role"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::monash-econ-wps/*"
        }
    ]
}
```