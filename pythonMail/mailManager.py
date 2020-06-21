import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import time
import re
import imaplib
import email
from email.header import decode_header
import os
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser

def construct_msg(account, reciever):
    message = MIMEMultipart()
    message['From'] = account
    message['Subject'] = input("Input Subject: ") 
    message['To'] = reciever
    print("Input Contents:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError: 
            break
        lines.append(line)
    mail_content = '\n'.join(lines);
    message.attach(MIMEText(mail_content, "plain"))
    return message, mail_content


def send_msg(account, password, dir_path):
    reciever = input("Input Reciever: ")
    msg, body= construct_msg(account, reciever)

    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    try:
        session.login(account, password) #login with mail_id and password
    except:
        print("Wrong account or password!!!")

    text = msg.as_string()
    try:
        session.sendmail(account, reciever, text)
    except:
        print("Something wrong, mail is unable to be sent!")
        session.quit()
        return

    print('Successfully sent mail.')
    now = datetime.now().time()
    now = parser.parse(str(now)).strftime('%d %B %Y at %H:%M')
    ID_file = open(os.path.join(dir_path, 'sended_cnt'), "r")
    ID = str(int(ID_file.read()) + 1)
    ID_file.close()
    lines = ["From: "+account.split('@')[0], "Date: "+now, "Message-ID: "+ID, 
            "Subject: "+msg['Subject'] ,"To: "+reciever.split('@')[0], "Content:", body]
    lines = '\n'.join(lines)
    f = open(os.path.join(dir_path, "mail" + ID), "w")
    f.write(lines)
    f.close()
    ID_file = open(os.path.join(dir_path, 'sended_cnt'), "w")
    ID_file.write(ID)
    ID_file.close()
    session.quit()
    return

def load_header(field_name, msg):
    try:
        de_field = decode_header(msg[field_name])[0]
    except:
        print("Error: cannot decode", field_name, ",which is", msg[field_name])
        return "None"
    field = de_field[0] 
    charset = de_field[1]
    if isinstance(field, bytes):
        try:
            if charset == 'None': 
                field = field.decode()
            else: 
                field = field.decode(charset)
        except:
            print("Error: Cannot decode", charset, "text")
            return "unknown"
    return field

def extract_content(msg):
    lines = []
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposiion"))
            try:
                body = part.get_payload(decode=True).decode()
            except:
                continue
            if content_type == "text/plain" and "attachment" not in content_disposition:
                lines.append(body)
            elif content_type == "text/html" and "attachment" not in content_disposition:
                soup = BeautifulSoup(body, features="html.parser")
                lines.append(soup.get_text('\n'))
            elif "attachment" in content_disposition: # download attachment
                filename = part.get_filename()
                print("attachments:", filename)
    else:
        content_type = msg.get_content_type()
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            body = msg.get_payload(decode=False)
        if content_type == "text/plain":
            lines.append(body)
        if content_type == "text/html":
            soup = BeautifulSoup(body, features="html.parser")
            lines.append(soup.get_text('\n'))
    lines = '\n'.join(lines)
    return lines

def read_gmail(account, password, dir_path, startID, read_N):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        mail.login(account, password)
    except:
        print("Wrong account or password!!!")
        return

    status, msgs = mail.select('inbox')
    mail_ids = int(msgs[0])
    latest = mail_ids
    oldest = 0
    for i in range(latest, max(0, latest - read_N), -1):
        response, msg = mail.fetch(str(i), '(RFC822)')
        for res_part in  msg:
            if(isinstance(res_part, tuple)):
                msg = email.message_from_bytes(res_part[1])
                msg_subject = load_header("Subject", msg)
                msg_from = load_header("From", msg)
                msg_to = load_header("To", msg).split('@')[0]
                msg_date = parser.parse(msg['Date']).strftime('%d %B %Y at %H:%M')
                
                msg_from = re.sub('[^0-9a-zA-Z]+', ' ', msg_from).split(' ')[0]
                msg_to = re.sub('[^0-9a-zA-Z]+', ' ', msg_from).split(' ')[0]
                msg_content =  extract_content(msg) 
                
               #print("-"*50)
                #print('From: ', msg_from)
                #print('Date:', msg_date)
                #print( 'Subject: ', msg_subject)
                #print('To:', msg_to)
                #extract_msg_content(msg);
                #print("-"*50)
                
                
                ID = str(latest - i + startID) 
                print("load mail" + ID)
                lines = ["From: "+msg_from, "Date: "+msg_date, "Message-ID: "+ID,
                        "Subject: "+msg_subject, "To: "+msg_to, "Content:", msg_content]
                lines = '\n'.join(lines)
                f = open(os.path.join(dir_path, "mail" + ID), "w")
                f.write(lines)
                f.close()
    return



if __name__ == "__main__":
    account = input("Input gmail account: ")
    password = getpass.getpass("Input gmail password: ")
   
    read_N = int(input("Input how many mails you want to load: "))

    default_dir = "./mailData"# This should be replaced with different dir for Qt to search
    if not os.path.isdir(default_dir):
        os.mkdir(default_dir)
        f = open(os.path.join(default_dir, "sended_cnt"), "w")
        f.write("0")
        f.close()
    f = open(os.path.join(default_dir, "sended_cnt"), "r")
    startID = int(f.read()) + 1024
    f.close()

    print("default_dir:", default_dir)
    read_gmail(account, password, default_dir, startID, read_N)
    while True:
        print("[0] send Mail,    [1] reload mails,     [2]stop")
        op = int(input("Input operation: "))
        if op == 0:
            send_msg(account, password, default_dir)
        elif op == 1:
            read_N = int(input("Input reload count:"))
            read_gmail(account, password, default_dir, startID, read_N)
        else:
            break
            
    print("Successfully Ending") 
