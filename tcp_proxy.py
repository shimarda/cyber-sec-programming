import sys
import socket
import threading

def hexdump(src, length=16):
    res = []
    digits = 4 if isinstance(src, bytes) else 2

    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = b' '.join("")

def proxy_handler(client_socket, remote_host, receive_first):

    #リモートホストへの接続
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    #必要ならリモートホストからデータを受信
    #リモート側から先にデータを受け取る必要があるか確認を行う
    if receive_first:

        #receive_fromはリモート側からのデータ受信、ローカル側からのデータ受信の両方に用いる
        remote_buf = receive_from(remote_socket)
        #この関数はデータの中身を表示する
        hexdump(remote_buf)

        #受信データ処理関数にデータを受け渡し
        #response_handlerではパケットの書き換え、ファジングテストの実施、認証における問題のテストなど
        #リモートから受信したデータに対してやりたいことを何でもできる
        remote_buf = response_handler(remote_buf)

        #もしローカル側に対して送るデータがあれば送信
        if len(remote_buf):
            print("<== Sending %d bytes to localhost.", len(remote_buf))
            client_socket.send(remote_buf)
    
    #ローカルからのデータ受信、リモートへの送信、ローカルへの送信
    while True:
        #ローカルホストからデータ受信
        local_buf = receive_from(client_socket)

        if len(local_buf):
            print("==> Received %d bytes from localhost.", len(local_buf))
            hexdump(local_buf)

            #送信データ処理関数にデータ受け渡し
            #response_handler同様にリモートへの送信パケットについて書き換えなどが出来る
            local_buf = request_handler(local_buf)

            #リモートホストへのデータ送信
            remote_socket.send(local_buf)
            print("==> Sent to remote.")
        
        #応答の受信
        remote_buf = receive_from(remote_socket)

        if len(remote_buf):
            print("<== Received %d bytes from remote.", len(remote_buf))
            hexdump(remote_buf)

            #受信データ処理関数にデータ受け渡し
            remote_buf = response_handler(remote_buf)

            #ローカル側に応答データを送信
            client_socket.send(remote_buf)
            print("<== Sent to localhost.")
        
        #ローカル側・リモート側双方からデータが来なければ接続終了
        if not len(local_buf) or not len(remote_buf):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connection.")

            break

def server_loop(local_host, local_port, remort_host, remort_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except:
        print("[!!] Failed to listen on %s:%d", local_host, local_port)
        print("[!!] Check for other listening sockets or correct permissions")
        sys.exit(0)
    
    print("[*] Listening on %s:%d", local_host, local_port)

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        #ローカル側からの接続情報を表示
        print("[==>] Received incoming connection from %s:%d", addr[0], addr[1])

        #リモートホストと通信するためのスレッドを開始
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_socket, remort_host, receive_first))

        proxy_thread.start()


if __name__ == "__main__":

    #コマンドライン引数の解釈
    if len(sys.argv[1:]) != 5:
        print("Usage: ./tcp_proxy.py [localhost] [localport] [remotehost] [remoteport] [receive first]")
        print("Example: ./tcp_proxy.py 111.0.0.1 9999 123.456.789.1 9999 True")
        sys.exit(0)

    #ローカル側での通信傍受を行うための設定
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    #リモート側の設定
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    #リモートにデータを送る前にデータ受信を行うかどうか
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    #通信待機ソケットの起動
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)