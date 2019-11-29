import os
import random
import smtplib
import pandas as pd
import jinja2

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
SMTP = None
BASE_DIR = os.getcwd()

def print_heading() -> None:
    """Prints out the application heading"""
    print("*" * 49 + " Welcome to Secret Santa " + "*" * 49)

def build_pandas_dataframe(filepath: str) -> DataFrame:
    """ Creates a pandas dataframe from a given filepath

    :param filepath: Path to CSV file that will be read into a dataframe
    :type filepath: str
    :returns: Pandas Data frame from a given filepath
    :rtype: DataFrame
    """
    df = pd.read_csv(filepath)
    return df


def render_template(template, **kwargs):
    ''' renders a Jinja template into HTML '''
    # check if template exists
    if not os.path.exists(template):
        print('No template file present: %s' % template)
        sys.exit()

    import jinja2
    templateLoader = jinja2.FileSystemLoader(searchpath="/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(**kwargs)


def email_gifter(gifter: dict) -> None:
    """ Emails gifter who they are shopping for and their list

    :param gifter: The person that is purchasing the gift
    :type gifter: dict
    """
    to = gifter['email']
    to_name = gifter['name']
    selected_name = gifter['selected']['name']
    shopping_list = gifter['selected']['shopping_list']
    body = render_template(
        f'{BASE_DIR}/email.tmpl', 
        vars={
            'to_name': to_name,
            'selected_name': selected_name,
            'shopping_list': shopping_list
        }
    )

    msg = MIMEMultipart()
    msg['To'] = to
    msg['From'] = GMAIL_USER
    msg['Subject'] = 'Family Secret Santa'
    msg.attach(MIMEText(body, 'html'))

    message = msg.as_string()

    try:
        SMTP = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        SMTP.login(GMAIL_USER, GMAIL_PASSWORD)
        SMTP.sendmail(GMAIL_USER, to, message)
        SMTP.close()

        print(f'Email sent to {to}!')
    except:
        print(f'Could not send to {to}!')

def get_selection_list(family: dict) -> dict:
    """ Builds the selection list for each secret santa participant 
    
    :param family: Family members participating in secret santa
    :type family: dict
    :returns: Selection List 
    :rtype: dict
    """
    # Selection list of participants
    secret_santa = family
    selection_list = []
    for k in secret_santa.keys():
        selection_list.append(k)

    for k in secret_santa.keys():
        while True:
            selected = random.choice(selection_list)
            if selected not in secret_santa[k]['exclusions'] and selected != k:
                secret_santa[k]['selected'] = {
                    'name': selected,
                    'shopping_list': secret_santa[selected][
                        'shopping_list'].split(',')
                }
                index = selection_list.index(selected)
                selection_list.pop(index)
                break
    
    return secret_santa

if __name__ == '__main__':
    print_heading()

    df = build_pandas_dataframe('family.csv')
    df = df.fillna('')
    df['exclusions'] = df['exclusions'].str.split(',')

    # df flattened into a dictionary
    family = {}
    for idx, row in df.iterrows():
        family[row['name']] = row
        family[row['name']]['selected'] = ''
    
    family = get_selection_list(family)
    
    for k in family.keys():
        email_gifter(family[k])
            