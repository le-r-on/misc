import argparse
import getpass
import logging
import random
import smtplib
import sys
import time

import requests


def confugure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = confugure_logging()


session = requests.Session()
BASE_URL = 'http://booking.uz.gov.ua/en/'
SEARCH_URL = 'https://booking.uz.gov.ua/en/purchase/search/'
PASSWORD = ''

trans = {
    '$$$': '7',
    '$$$$': 'f',
    '$$$_': 'e',
    '$$_': '6',
    '$$_$': 'd',
    '$$__': 'c',
    '$_$': '5',
    '$_$$': 'b',
    '$_$_': 'a',
    '$__': '4',
    '$__$': '9',
    '$___': '8',
    '_$$': '3',
    '_$_': '2',
    '__$': '1',
    '___': '0',
}


def get_token_and_cookie():
    resp = session.get(BASE_URL)

    body = resp.text.encode('iso-8859-1', errors='ignore')
    start_idx = body.find(r'"\\\""+') + 7
    end_idx = body.find(r'+"\\\"', start_idx)

    obfuscated_token = body[start_idx:end_idx]
    token = []
    for elem in obfuscated_token.split('+'):
        token.append(trans[elem.split('.')[1]])
    return ''.join(token)

def send_notification(msg):
    fromaddr = 'bodnarchuk.roman@gmail.com'
    toaddrs  = 'bodnarchuk.roman@gmail.com'

    # Credentials (if needed)
    username = 'bodnarchuk.roman@gmail.com'

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, PASSWORD)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

def main():
    parser = argparse.ArgumentParser(description='Monitor UZ tickets.')
    parser.add_argument('--from-station', help='From station, int', required=True)
    parser.add_argument('--to-station', help='To station, int', required=True)
    parser.add_argument('--date', help='Departure date, like 16.05.2015', required=True)

    args = parser.parse_args()

    global PASSWORD
    PASSWORD = getpass.getpass('gmail password >')
    send_notification('Started!')

    while True:
        try:
            execute(from_station=args.from_station, to_station=args.to_station, date=args.date)
        except Exception:
            logger.exception('Unexpected error, restarting')
            time.sleep(30)


def execute(from_station, to_station, date):
    token = get_token_and_cookie()
    data = dict(
        station_id_from=from_station,
        station_id_till=to_station,
        date_dep=date,
        time_dep='00:00',
        time_dep_till='',
        another_ec='0',
        search='',
    )

    headers = {
        'GV-Token': token,
        'GV-Ajax': '1',
        'GV-Referer': 'http://booking.uz.gov.ua/en/',
    }

    resp = None
    found = False
    try:
        while True:
            resp = session.post(SEARCH_URL, data=data, headers=headers, timeout=3)
            result = resp.json()
            if not result.get('error'):
                logger.info('Found train! {}'.format(result))
                if not found:
                    send_notification(result)
                    found = True
            else:
                found = False
            time.sleep(random.randint(3, 7))
            logger.info('Alive')
    finally:
        if resp is not None:
            logger.warning('Latest response: {}'.format(resp.text))


if __name__ == '__main__':
    main()