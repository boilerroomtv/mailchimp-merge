import os
import json
import requests
from requests.auth import HTTPBasicAuth
import tablib
import logging
import sys
from chalk import white, red, RESET

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger()

KEY = os.environ['MAILCHIMP_KEY']
DATACENTER = os.environ['MAILCHIMP_DATACENTER']

EXPORT_URL = 'https://{}.api.mailchimp.com/export/1.0/list/'.format(DATACENTER)
LISTS_URL = 'https://{}.api.mailchimp.com/3.0/lists/'.format(DATACENTER)

PAGE_SIZE = 100

EMAIL_ADDRESS = 'Email Address'
FIRST_NAME = 'First Name'
LAST_NAME = 'Last Name'
PHONE_NUMBER = 'Phone Number'
HEADERS = [EMAIL_ADDRESS, FIRST_NAME, LAST_NAME, PHONE_NUMBER, 'Original list ID']


def extract_header_info(data, list_id):
    try:
        email_index = data.index(EMAIL_ADDRESS)
    except ValueError:
        try:
            email_index = data.index('{}*'.format(EMAIL_ADDRESS))
        except ValueError:
            logger.warning(white('WARNING CANNOT FIND {} IN {}'.format(red('EMAIL'), list_id), bold=True) + RESET)
            logger.warning(data)
            email_index = None
    try:
        first_index = data.index(FIRST_NAME)
    except ValueError:
        try:
            first_index = data.index('{}*'.format(FIRST_NAME))
        except ValueError:
            logger.warning(white('WARNING CANNOT FIND {} IN {}'.format(red('FIRST NAME'), list_id), bold=True) + RESET)
            logger.warning(data)
            first_index = None
    try:
        last_index = data.index(LAST_NAME)
    except ValueError:
        try:
            last_index = data.index('{}*'.format(LAST_NAME))
        except ValueError:
            logger.warning(white('WARNING CANNOT FIND {} IN {}'.format(red('LAST NAME'), list_id), bold=True) + RESET)
            logger.warning(data)
            last_index = None
    try:
        phone_index = data.index(PHONE_NUMBER)
    except ValueError:
        try:
            phone_index = data.index('{}*'.format(PHONE_NUMBER))
        except ValueError:
            logger.warning(white('WARNING CANNOT FIND {} IN {}'.format(red('PHONE'), list_id), bold=True) + RESET)
            logger.warning(data)
            phone_index = None
    return email_index, first_index, last_index, phone_index


def extract_data(data, indexes):
    row = ()
    for index in indexes:
        if index is not None:
            row += (data[index],)
        else:
            row += ('',)
    return row


def get_list(list_id):
    payload = {
        'apikey': KEY,
        'id': list_id,

    }
    r = requests.post(EXPORT_URL, data=json.dumps(payload), stream=True)
    r.raise_for_status()
    indexes = (None, None, None, None,)
    header = True
    for line in r.iter_lines():
        # filter out keep-alive new lines
        if line:
            decoded_line = line.decode('utf-8')
            data = json.loads(decoded_line)
            if header:
                indexes = extract_header_info(data, list_id)
                header = False
            else:
                yield extract_data(data, indexes) + (list_id,)


def get_list_raw(list_id):
    payload = {
        'apikey': KEY,
        'id': list_id,

    }
    r = requests.post(EXPORT_URL, data=json.dumps(payload), stream=True)
    r.raise_for_status()
    for line in r.iter_lines():
        # filter out keep-alive new lines
        if line:
            decoded_line = line.decode('utf-8')
            yield json.loads(decoded_line)


def _get_lists(offset=0):
    payload = {
        'fields': 'lists.id,lists.name,total_items',
        'count': PAGE_SIZE,
        'offset': offset
    }
    r = requests.get(LISTS_URL, params=payload, auth=HTTPBasicAuth('lol', KEY))
    r.raise_for_status()
    return r.json()


def get_lists():
    more_items = True
    offset = 0
    while more_items:
        results = _get_lists(offset)
        total_items = results['total_items']
        for result in results['lists']:
            yield result['id'], result['name']
        more_items = (offset + PAGE_SIZE) < total_items
        offset += PAGE_SIZE


def main():
    results = tablib.Dataset(headers=HEADERS)
    for list_id, name in get_lists():
        logger.info('List ID: {id}\tList name: {name}'.format(id=list_id, name=name))
        for row in get_list(list_id):
            results.append(row)

    return results.export('csv', delimiter='\t')


def backup_lists():
    for list_id, name in get_lists():
        logger.info('List ID: {id}\tList name: {name}'.format(id=list_id, name=name))
        with open('{} - {} - BACKUP.json'.format(list_id, name), 'w') as f:
            for row in get_list_raw(list_id):
                f.write('\t'.join(str(cell) for cell in row))
                f.write('\n')


if __name__ == '__main__':
    try:
        print(main())
    except:
        logger.exception('Unhandled error!')
