from selenium import webdriver
from datetime import datetime, timezone, timedelta
import re, requests, json
import urllib.request, urllib.error
import boto3

s3 = boto3.resource('s3')

LINE_TOKEN = "${channel_token}''


# S3書き込み
def write_s3(text, bucket, key):
    bucket = bucket # バケット名
    contents = text
    obj = s3.Object(bucket,key)
    obj.put(Body=contents)
    return

# S3取得
def get_s3(bucket, key):
    bucket = bucket # バケット名
    obj = s3.Object(bucket,key)
    response = obj.get()  
    body = response['Body'].read()
    return body.decode('utf-8')

# 現在の日時を取得
def get_current_time():
    # タイムゾーンを設定（例: 日本のタイムゾーン JST）
    jst = timezone(timedelta(hours=+9))
    current_time = datetime.now(jst)
    # 日時を文字列にフォーマット
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time
    
# 年、月、日が一致するか確認
def is_same_date(date_str1, date_str2):
    # 日付文字列をdatetimeオブジェクトに変換
    date1 = datetime.strptime(date_str1, "%Y-%m-%d %H:%M:%S")
    date2 = datetime.strptime(date_str2, "%Y-%m-%d %H:%M:%S")
    return date1.year == date2.year and date1.month == date2.month and date1.day == date2.day
    
# LINEに通知する
def send_line_broadcast(message, token):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    # messageの中にtype,textの配列を追加すれば一度に複数のメッセージを送信できます。(最大件数5)
    data = {
        'messages' : [{
            'type':'text',
            'text': message
        }]
    }
    jsonstr = json.dumps(data).encode('ascii')
    request = urllib.request.Request(url, data=jsonstr)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Authorization', 'Bearer ' + token)
    request.get_method = lambda: 'POST'
    response = urllib.request.urlopen(request)

def lambda_handler(event, context):
    URL = "https://donmaru-hiratsuka.com/info"

    options = webdriver.ChromeOptions()
    # headless-chromiumのパスを指定
    options.binary_location = "/opt/headless/headless-chromium"
    options.add_argument("--headless")
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        # chromedriverのパスを指定
        executable_path="/opt/headless/chromedriver",
        options=options
    )
    
    driver.get(URL)
    title = driver.title

    xpath = f'//*[@id="main_inner"]/div[1]/div/div[1]/div[1]'
    info_date = driver.find_element_by_xpath(xpath)
    info_date_text = info_date.text
    print('info_date_text: ' + info_date_text)
    
    xpath = f'//*[@id="main_inner"]/div[1]/div/div[1]/div[2]/a'
    info_title = driver.find_element_by_xpath(xpath)
    info_title_text = info_title.text
    print('info_title: ' + info_title.text)
    
    xpath = f'//*[@id="main_inner"]/div[1]/div/div[1]/div[3]'
    info_body = driver.find_element_by_xpath(xpath)
    info_body_text = info_body.text
    print('info_body: ' + info_body.text)
    
    driver.close()
    
    current_time = get_current_time()
    past_title = get_s3('ksato-develop', '丼丸/log.txt')
    print('current_time: ' + current_time)
    print('past_title: ' + past_title)
    if is_same_date(info_date_text, current_time) and past_title != info_title_text:
        message = '<' + info_title_text + '>' + '\n\n' + info_body_text
        send_line_broadcast(message, LINE_TOKEN)
        write_s3(info_title_text, 'ksato-develop', '丼丸/log.txt')
        print('Line sent')
    
    return title
