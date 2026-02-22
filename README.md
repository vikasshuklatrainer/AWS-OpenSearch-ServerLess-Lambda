# AWS-OpenSearch-ServerLess-Lambda

In This lab we will create a Lambda function that will sends the data to AWS open search server less collection.

## Create a Open Search Server-less collection

Go to AWS Console 

![1](./images/1.png)

From the left panel, Select "collections".

![2](./images/2.png)

Click on Create Collection.

![3](./images/3.png)

Provide a name to Collection and Select "search"

![4](./images/4.png)

un select the  redundancy check box and select standard create.

![5](./images/5.png)

Select Network access public. Check both resource type and click next.

![6](./images/6.png)

Select appropriate data access  permissions.  
![7](./images/7.png)

Save it as a new policy and click next.

![8](./images/8.png)

Name the Index as "" demo-index
![9](./images/9.png)

Review and click Submit.

![10](./images/10.png)

wait for collection to be created. Do not navigate away  from this page.
![11](./images/11.png)

Once your open search collection will be ready screen will look like . Note down the open search endpoint. and dashboard url. we will need this later on.

![12](./images/12.png)

Click on Dashboard Url , and you will see the dashboard.
![13](./images/13.png)

---

### Create Lambda Function that will send Data o this open search

First Create a IAM Role that Lambda will use to connect with AWS opensearch collection.

Create a Policy Name "Shukla-lambda-OSS-access-policy".
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "aoss:APIAccessAll",
            "Resource": "*"
        }
    ]
}
```

![Policy 1](./images/policy-1.png)

Create a Role for Lambda and assign permission and policy on it.
![Role 1](./images/Role-1.png)

## Lets create a Lambda and Assign the role and permission to it.

Go to AWS console and search form Lambda
![Lambda 1](./images/lambda-1.png)
![Lambda 2](./images/lambda-2.png)
use previously created Role to assign to this lambda. and click createe
![Lambda 3](./images/lambda-3.png)
![Lambda 4](./images/lambda-4.png)

Our lambda function is created in python , this will generate some random data and insert that data in previously created open search collection.

This code has some dependency. these dependencies can not be directly input in the code. AWS lambda use provides a concept of layers to manage it.

### Lets create a layers that can be used in this lambda

![Layer 1](./images/layer-1.png)
![Layer 2](./images/layer-2.png)
Layer is now ready to reuse.
![Layer 3](./images/layer-3.png)

### Lets add this layer in our lambda
Go to the Lambda and click on layers.
![Lambda 5](./images/lambda-5.png)

Click on Add a layer.
![Lambda 6](./images/lambda-6.png)
Select the previously added layer from the drop down.  Click Add
  
![Lambda 7](./images/lambda-7.png)

Layer is now successfully Added to the Lambda.
![Lambda 8](./images/lambda-8.png)







