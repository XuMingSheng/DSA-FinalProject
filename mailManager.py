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

def filter(s):
    return re.sub(r"[^\x00-\x7F]+", " ", s)

def construct_msg(account, reciever):
    message = MIMEMultipart()
    message['From'] = account
    message['Subject'] = read_fifo("Input Subject: \n") 
    message['To'] = reciever
    #write_fifo("Please input contents: \n")
    lines = []
    while True:
        line = read_fifo("Input content: \n")
        if line == 'END\n':
            break
        lines.append(line)
    mail_content = '\n'.join(lines);
    message.attach(MIMEText(mail_content, "plain"))
    return message, mail_content


def send_msg(account, password, dir_path):
    reciever = read_fifo("Input Reciever: \n")
    msg, body= construct_msg(account, reciever)

    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    try:
        session.login(account, password) #login with mail_id and password
    except:
        write_fifo(password)
        write_fifo("1\n")
 
    text = msg.as_string()
    try:
        session.sendmail(account, reciever, text)
    except:
        write_fifo("Error: Something wrong, mail is unable to be sent!\n")
        read_fifo("NULL")
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
        #write_fifo("Error: cannot decode " + field_name + "\n")
        return "unknown"
    field = de_field[0] 
    charset = de_field[1]
    if isinstance(field, bytes):
        try:
            if charset == 'None': 
                field = field.decode()
            else: 
                field = field.decode(charset)
        except:
            #write_fifo("Error: Cannot decode " + str(charset) + "text \n")
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

def read_gmail(account, password, dir_path, startID):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    print("acct:", account)
    print("pass:", password)
    try:
        mail.login(account, password)
    except:
        #write_fifo("wrong: " + password)
        #write_fifo("Error: wrong pass or account\n")
        return 1
    
    while True:
        try:
            read_N = int(read_fifo("Input how many mails you want to load: \n"))
            break
        except:
            write_fifo("Error: It is not a integer!!! (or other errors)\n") 

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
                msg_content = extract_content(msg)
                
                msg_from = filter(msg_from)
                msg_to = filter(msg_to)
                msg_subject = filter(msg_subject)
                msg_content = filter(msg_content)[:1000]
                
                msg_from = msg_from.rstrip("\r\n")
                msg_to = msg_to.rstrip("\r\n")
                msg_subject = msg_subject.rstrip("\r\n") + ' '
                msg_from = msg_from.replace("\t","")
                msg_to = msg_to.replace("\t","")
                msg_content = msg_content.replace("\r\n","") 
                
                if msg_from.strip() == '':  
                    msg_from = "unknown"
                if msg_to.strip() == '':
                    msg_to = "unknown"
                if msg_subject.strip() == '':
                    msg_subject = "unknown "

                print("-"*50)
                print('From: ', msg_from)
                print('Date:', msg_date)
                print( 'Subject: ', msg_subject)
                print('To:', msg_to)
                #extract_content(msg);
                print("-"*50)
                
                
                ID = str(latest - i + startID) 
                #write_fifo("load mail" + ID + "\n")
                lines = ["From: "+msg_from, "Date: "+msg_date, "Message-ID: "+ID,
                        "Subject: "+msg_subject, "To: "+msg_to, "Content:", msg_content]
                lines = '\n'.join(lines)
                f = open(os.path.join(dir_path, "mail" + ID), "w")
                f.write(lines)
                f.close()
    return 0

def read_fifo(msg):
    if msg != "NULL":
        write_fifo(msg)
    FIFO_PATH = '/tmp/mail_in_pipe'
    fifo = open(FIFO_PATH, 'r')
    for line in fifo:
        s = line
        #print(s)
    fifo.close()
    return s

def write_fifo(s):
    FIFO_PATH = '/tmp/mail_out_pipe'
    fifo = open(FIFO_PATH, 'w')
    fifo.write(s)
    fifo.close()
    time.sleep(0.5)
    return 

if __name__ == "__main__":
    print("haha")
    default_dir = read_fifo("Input mail_dir: \n")[:-1]
    #default_dir = "./mailData"# This should be replaced with different dir for Qt to search
    if not os.path.isdir(default_dir):
        os.mkdir(default_dir)
        f = open(os.path.join(default_dir, "sended_cnt"), "w")
        f.write("0")
        f.close()
    f = open(os.path.join(default_dir, "sended_cnt"), "r")
    startID = int(f.read()) + 1024
    f.close()
  
     
    account = read_fifo("input gmail account: \n")[:-1]
    password = read_fifo("Input gmail password: \n")[:-1]
    result = read_gmail(account, password, default_dir, startID)
    while result == 1:
        account = read_fifo("Error, RE-input gmail account\n")[:-1]
        password = read_fifo("Input gmail password\n")[:-1]
        result = read_gmail(account, password, default_dir, startID)
        
    while True:
        #write_fifo("[0] send Mail,    [1] reload mails,     [2]stop\n")
        try:
            op = int(read_fifo("Input operation: \n"))
        except:
            break
        if op == 0:
            send_msg(account, password, default_dir)
        elif op == 1:
            read_gmail(account, password, default_dir, startID)
        else:
            break
            
    write_fifo("Successfully Ending\n") 
