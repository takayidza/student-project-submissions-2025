Version
-------

3.0

Overview
--------

Compare two faces and decide whether they are from the same person. You can upload image file or use face\_token for face comparing. For image upload, the biggest face by the size of bounding box within the image will be used. For face\_token, you shall get it by using Detect API.

### Image Requirements

Format : JPG (JPEG), PNG  
Size : between 48\*48 and 4096\*4096 (pixels)  
File size : no larger than 2MB  
Minimal size of face : the bounding box of a detected face is a square. The minimal side length of a square should be no less than 150 pixels.

### Changelog

March 28, 2017. Added support for Base64 encoded image.

Request URL
-----------

https://api-us.faceplusplus.com/facepp/v3/compare

Request Method
--------------

POST

Permission
----------

All API Keys can use this API.

Request Parameter
-----------------

Name

Type

Description

Required

api\_key

String

Your registered API Key to call this API

Required

api\_secret

String

Your registered API Secret to call this API

Required (choose any of four)

face\_token1

String

The id of the first face. (Highest precedence)

image\_url1

String

URL of the first image.

image\_file1

File

The binary data of the first image, uploaded via POST multipart/form-data.

image\_base64\_1

String

Base64 encoded binary data of the first image.

These three parameters (image\_url1, image\_file1 and image\_base64\_1) will be adopted in the following order of precedence:

Highest: image\_file1; Lowest: image\_url1.

Required (choose any of four)

  

face\_token2

String

The id of the second face

image\_url2

String

URL of the second image.

image\_file2

File

The binary data of the second image, uploaded via POST multipart/form-data.

image\_base64\_2

String

Base64 encoded binary data of the second image.

These three parameters (image\_url2, image\_file2 and image\_base64\_2) will be adopted in the following order of precedence:

Highest: image\_file2; Lowest: image\_url2.

Return Values
-------------

Fields

Type

Description

request\_id

String

Unique id of each request

confidence

Float

Indicates the similarity of two faces, a floating-point number with 3 decimal places between \[0,100\]. Higher confidence indicates higher possibility that two faces belong to same person.

Note: if no face is detected within the image uploaded, this string will not be returned.

thresholds

Object

A set of thresholds including 3 floating-point numbers with 3 decimal places between \[0,100\].

If the confidence does not meet the "1e-3" threshold, it is highly suggested that the two faces are not from the same person. While if the confidence is beyond the "1e-5" threshold, there's high possibility that they are from the same person.

1e-3: confidence threshold at the 0.1% error rate;

1e-4: confidence threshold at the 0.01% error rate;

1e-5: confidence threshold at the 0.001% error rate;

Note: seeing that thresholds are not static, there's no need to store values of thresholds in a persistent form, especially not to compare the confidence with a previously returned threshold.

 If no face is detected within the image uploaded, this string will not be returned.

image\_id1

String

Unique id of an image uploaded by image\_url1, image\_file1 or image\_base64\_1.

Note: if none of image\_url1, image\_file1 or image\_base64\_1 is used, this string will not be returned.

image\_id2

String

Unique id of an image uploaded by image\_url2, image\_file2 or image\_base64\_2.

Note: if none of image\_url2, image\_file2 or image\_base64\_2 is used, this string will not be returned.

faces1

Array

Array of detected faces within the image uploaded by image\_url1, image\_file1 or image\_base64\_1. The first face in this array will be used for face comparing.

Note: if none of image\_url1, image\_file1 or image\_base64\_1 is used, this array will not be returned. If no face is detected, the array is \[\].

faces2

Array

Array of detected faces within the image uploaded by image\_url2, image\_file2 or image\_base64\_2. The first face in this array will be used for face comparing.

Note: if none of image\_url2, image\_file2 or image\_base64\_2 is used, this array will not be returned. If no face is detected, the array is \[\].

time\_used

Int

Time that the whole request takes. Unit: millisecond

error\_message

String

This string will not be returned unless request fails. For more details, please see the following section on error message.

### Elements contained in faces array

Fields

Type

Description

face\_token

String

Unique id of the detected face

face\_rectangle

Object

A rectangle area for the face location on image. The following coordinates are all integer numbers:

top：Y-coordinate of upper left corner

left：X-coordinate of upper left corner

width：The width of the rectangle frame

height：The height of the rectangle frame

Sample response
---------------

### Sample response when request has succeeded:

{
  "time\_used": 473,
  "confidence": 96.46,
  "thresholds": {
    "1e-3": 65.3,
    "1e-5": 76.5,
    "1e-4": 71.8
  },
  "request\_id": "1469761507,07174361-027c-46e1-811f-ba0909760b18"
}

### Sample response when request has failed:

{
  "time\_used": 5,
  "error\_message": "INVALID\_FACE\_TOKEN:c2fc0ad7c8da3af5a34b9c70ff764da0",
  "request\_id": "1469761051,ec285c20-8660-47d3-8b91-5dc2bffa0049"
}

Unique ERROR\_MESSAGE of this API
---------------------------------

HTTP Status Code

Error Message

Description

400

INVALID\_FACE\_TOKEN: <face\_token>

face\_token can not be found

400

IMAGE\_ERROR\_UNSUPPORTED\_FORMAT:<param>

The image which <param> indicates can not be resolved. The file format may not be supported or the file is damaged.

400

INVALID\_IMAGE\_SIZE:<param>

The size of uploaded image does not meet the requirement as above. <param> is the argument which indicates its size of image is too big.

400

INVALID\_IMAGE\_URL: <param>

Failed downloading image from URL which <param> indicates. The image URL is wrong or invalid.

400

IMAGE\_FILE\_TOO\_LARGE:<param>

The image file passed by <param> is too large. This API requires image file size to be no larger than 2 MB.

412

IMAGE\_DOWNLOAD\_TIMEOUT: <param>

Image download timeout

Common ERROR\_MESSAGE
---------------------

HTTP Status Code

Error Message

Description

401

AUTHENTICATION\_ERROR

api\_key and api\_secret does not match.

403

AUTHORIZATION\_ERROR:<reason>

api\_key does not have permission to call this API.

Values of <reason> are:

*   "Denied by Client"
    
*   "Denied by Admin"
    
*   "Insufficient Account Balance"
    

403

CONCURRENCY\_LIMIT\_EXCEEDED

The rate limit for this API Key has been exceeded.

Note: "rate limit" means the QPS capacity of each API Key. To raise QPS capacity of your API Key, please refer to [Face++ Pricing and Plans page](https://www.faceplusplus.com/pricing/) or contact us.

400

MISSING\_ARGUMENTS: <key>

Some required arguments missed.

400

BAD\_ARGUMENTS:<key>

Error while parsing some arguments. This error may be caused by illegal type or length of argument.

400

COEXISTENCE\_ARGUMENTS

Passed several arguments which are not allowed to coexist. This error message will be returned unless otherwise stated.

413

Request Entity Too Large

The request entity has exceeded the limit (2MB). This error message will be returned in plain text, instead of JSON.

404

API\_NOT\_FOUND

Requested API can not be found.

500

INTERNAL\_ERROR

Internal error. Please retry the request.

If this error keeps occurring, please contact our support team.

Sample request
--------------

curl -X POST "https://api-us.faceplusplus.com/facepp/v3/compare" \\
-F "api\_key=<api\_key>" \\
-F "api\_secret=<api\_secret>" \\
-F "face\_token1=c2fc0ad7c8da3af5a34b9c70ff764da0" \\
-F "face\_token2=ad248a809408b6320485ab4de13fe6a9"