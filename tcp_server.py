import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9998

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#接続を待つIPアドレスをポート番号を指定する
server.bind((bind_ip, bind_port))

#接続の待ち受けを開始する
server.listen()

print("[*] Listening on %s:%d", (bind_ip, bind_port))

#クライアントからの接続を処理するスレッド
def handle_client(client_socket):

    #クライアントが送信してきた接続を処理するスレッド
    request = client_socket.recv(1024)

    print("[*] Received: %s" % request)

    #パケットの送信
    client_socket.send(b"ACK")

    client_socket.close()

while True:

    #クライアントが接続してきたら
    #クライアントソケットのオブジェクトをclientへ、
    #クライアントの接続情報をaddrへ
    client, addr = server.accept()

    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    #受信データを処理するスレッドの起動
    client_handler = threading.Thread(target=handle_client, args= (client, ))
    client_handler.start()

