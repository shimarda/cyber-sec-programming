import socket

target_host = "0.0.0.0"
target_port = 9998

#ソケットオブジェクトの作成
#AF_INETはIPv4のアドレスやホスト名を使用する設定
#SOCK_STREAMのTCPを用いるための設定
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#サーバーへの接続
#
client.connect((target_host, target_port))

#データの送信
client.send(b"GET / HTTP/1.1\r\nHOST: 0.0.0.0\r\n\r\n")

#データの受信
response = client.recv(4096)

print(response)