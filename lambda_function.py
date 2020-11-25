import json
import io
import logging
import base64
import boto3
import pdfkit
import urllib.parse
import datetime
from PyPDF2 import PdfFileMerger, PdfFileReader

BUCKET = 'monash-econ-wps'
DIR_LIST_PATH = 'RePEc/mos/moswps/index.html'
# TEMPLATE_PATH = 'template/wp_cover_static.png'
TEMPLATE_URL= 'https://github.com/sodalabsio/econ_working_paper_series/raw/main/monash-econ-wps/template/wp_cover_static.png'
HANDLE = 'RePEc:mos:moswps'

HTML = """
        <!DOCTYPE html>
        <html>
          <head>
            <title>Monash Econ WP Series</title>
            <link rel="preconnect" href="https://fonts.gstatic.com">
            <link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:ital,wght@0,300;0,400;0,700;1,300;1,400;1,700&display=swap" rel="stylesheet">
            <style>
            img {{
                height: 1500px
            }}
            .container {{
              position: relative;
            }}
            div.paper {{
                position: absolute;
                top: 290px;
                left: 125px;
                width: 823px;
                max-width: 823px;
            }}
            p {{
                color: #414141;
                font-family: 'Roboto Condensed';
            }}
            p.title {{
                border-style: solid none solid none;
                border-width: thin;
                font-size: 18pt;
                font-weight: 900;
                text-align: center;
                padding-top: 25px;
                padding-bottom: 25px;
            }}
            p.paper-no {{ 
                font-size: 15pt;
                text-align: center;
            }}
            p.author {{ 
                font-size: 18pt;
                text-align: center;
            }}
            p.abstract-fixed {{ 
                font-size: 15pt;
            }}
            p.abstract {{ 
                font-size: 15pt;
                text-align: justify;
            }}
            p.keywords {{ 
                font-size: 15pt;
                text-align: left;
            }}
            p.jel-codes {{ 
                font-size: 15pt;
                text-align: left;
            }}
            p.affiliation {{ 
                font-size: 15pt;
                text-align: left;
            }}
            </style>
          </head>
          <body>
            <div class="container">
              <img src="{}" alt="econ wp background"/>
              <div class="paper">
              <p class="title">{}</p>
              <p class="paper-no">Discussion Paper no. <a href='{}'>{}</a></p>
              <p class="author"><b>{}</b></p>
              <p class="abstract-fixed"><b>Abstract:</b></p>
              <p class="abstract">{}</p>
              <p class="keywords"><b>Keywords: </b>{}</p>
              <p class="jel-codes"><b>JEL Classification: </b>{}</p>
              <p class="affiliation">{}</p>
              </div>
              </div>
            </body>
        </html>
        """

s3 = boto3.client('s3', verify=False)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def read_from_bucket(bucket, key, is_json=True):
    """Read file from S3"""
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read().decode('utf-8')
    if is_json:
      data = json.loads(data)
    return data

def postprocess(file, file_path, config, **kwargs):
    """Method to postprocess HTML and merge with PDF"""
    file_content = base64.b64decode(file) # retrieve uploaded PDF file
    title = kwargs.get('title')
    abstract = kwargs.get('abstract')
    authors = kwargs.get('author')
    keywords = kwargs.get('keyword')
    jel_codes = kwargs.get('jel_code') 
    authors_inline = ""
    for i, author in enumerate(authors):
        if i != len(authors)-1:
            authors_inline += f"{author['name']}"
            if i != len(authors)-2: authors_inline += ", "
        else:
            authors_inline += f" and {author['name']}"
    
    affiliation = ""
    for i, author in enumerate(authors):
        affiliation += f"{author['name']}: {author['affiliation']} (email: <a href=\"mailto:{author['email']}\">{author['email']}</a>)"
        if i != len(authors)-1:
            affiliation += "; "
        else:
            affiliation += "."
    
    wpn = kwargs.get('wpn')
    # the link should point to https://monash-econ-wps.s3-ap-southeast-2.amazonaws.com/RePEc/mos/moswps/
    link = f'http://{BUCKET}.s3-ap-southeast-2.amazonaws.com/{file_path}'
    # ref = authors  + ' (' + wpn.split('-')[0] + '), ' +  'Monash Econ Working Paper Series No. ' + wpn + ', Monash Business School, available at ' + link
    pub_online = kwargs.get('pub_online') # get date/parse to dd mon yyy
    
    # add content to html
    # authors = ', '.join(authors)
    html = HTML.format(TEMPLATE_URL, title, link, wpn, authors_inline, abstract, keywords, jel_codes, affiliation)
    # convert html to pdf (bytes)
    # pdf = pdfkit.from_string(html, False) 
    pdf = pdfkit.from_string(html, False, configuration=config)
    
    # merge pdf + file
    output = io.BytesIO()
    mergedObject = PdfFileMerger()
    mergedObject.append(PdfFileReader(io.BytesIO(pdf)))
    mergedObject.append(PdfFileReader(io.BytesIO(file_content))) # error?
    mergedObject.write(output)
    
    return output.getvalue(), link
    
def create_rdf(link, handle, **kwargs):
    """Method to create RDFs
    reference: https://ideas.repec.org/t/papertemplate.html
    """
    title = kwargs.get('title')
    abstract = kwargs.get('abstract')
    authors = kwargs.get('author')
    email = kwargs.get('email')
    wpn = kwargs.get('wpn')
    pub_online = kwargs.get('pub_online')
    jel_code = kwargs.get('jel_code')
    keywords = kwargs.get('keyword')
    _, month, yyyy = pub_online.split(" ")
    datetime_object = datetime.datetime.strptime(month, "%B")
    mm = "{0:0=2d}".format(datetime_object.month)
    paper_date = yyyy + "-" + mm # yyyy-mm
    # workplace_name = "Department of Economics, Monash University"
    temp = "Template-Type: ReDIF-Paper 1.0\n" # template
    # add authors
    for author in authors:
        temp += "Author-Name: " + author['name'].strip() + "\n"
        temp += "Author-Email: " + author['email'] + "\n"
        temp += "Author-Workplace-Name: " + author['affiliation'] + "\n"
    
    # add title
    temp += "Title: " + title + "\n"
    # add abstract
    temp += "Abstract: " + abstract + "\n"
    # add creation date
    temp += "Creation-Date: " + paper_date + "\n" # yyyy-mm
    # add file-url
    temp += "File-URL: " + link + "\n"
    # add file-format
    temp += "File-Format: Application/pdf" + "\n"
    # add number - make sure they allow hyphens!
    temp += "Number: " + wpn + "\n"
    # add JEL code
    temp += "Classification-JEL: " + jel_code + "\n"
    # add keywords
    temp += "Keywords: " + keywords + "\n"
    # add handle
    temp += "Handle: " + handle + ":" + wpn + "\n"
    return temp

def lambda_handler(event, context):
    data = event['content']
    logger.info(data.keys())
    wpn = data['wpn']
    title = data['title']
    author = data['author'].split('|') # | is used as the delimiter
    author = [dict(name=author[i], affiliation=author[i+1], email=author[i+2]) for
                    i in range(0, len(author), 3)]
    keyword = data['keyword']
    jel_code = data['jel_code']
    abstract = urllib.parse.unquote(data['abstract']) # decodeURI
    file = data['file']
    pub_online = data['pub_online']
    logger.info('data received..')
    
    config = pdfkit.configuration(wkhtmltopdf='/opt/bin/wkhtmltopdf')
    logger.info('binaries found..')
    
    # dir_list_file = read_from_bucket(BUCKET, DIR_LIST_PATH, False)
    path = HANDLE.replace(':', '/') + f'/{wpn}'
    
    file_path = path + '.pdf'
    rdf_path = path + '.rdf'
    
    metadata = {'wpn' : wpn,
                'title': title,
                'year': int(wpn.split('-')[0]),
                'author': author,
                'keyword' : keyword,
                'jel_code': jel_code,
                'abstract' : abstract,
                'pub_online': pub_online
                }
    output, link = postprocess(file, file_path, config, **metadata)
    rdf = create_rdf(link, HANDLE, **metadata) # create RDF
    try:
        # upload processed PDF
        s3.put_object(Bucket=BUCKET, Key=file_path, Body=output, ContentType='application/pdf')
        # upload RDF file - to previous FTP location
        s3.put_object(Bucket=BUCKET, Key=rdf_path, Body=rdf)
        
        response = {
        "statusCode": 200,
        "headers": {
        "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
        "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS 
        },
        "body": {
            'msg': 'File: {} successfully processed.'.format(wpn),
            'url' : link
          }
        }
        return response
        
    except Exception as e:
        raise IOError(e)