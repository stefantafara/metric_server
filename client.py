import socket
import time


class ClientError(socket.error):
    pass


class Client:

    def __init__(self, host, port, timeout=None):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.sock.settimeout(timeout)

    def send(self, send_str):
        try:
            print("Sending data:", send_str)
            self.sock.sendall(send_str.encode("utf8"))
            print("Waiting for server response...")
            data = self.sock.recv(1024)
            return data.decode('utf-8')
        except socket.error as sock_err:
            return None

    def put(self, metric, metric_value, timestamp=None):
        # put palm.cpu 23.7 1150864247\n
        if timestamp is None:
            timestamp = int(time.time())
        send_str = "put {} {} {}\n".format(metric, metric_value, timestamp)
        response = self.send(send_str)
        if not response:
            raise ClientError
        else:
            print(f'Received response: {ascii(response)}')
        if response == "ok\n\n":
            print("Data has been successfully sent")
        elif response == "error\nwrong command\n\n":
            raise ClientError

    def get(self, metric):
        send_str = "get {}\n".format(metric)
        response = self.send(send_str)
        #ok\npalm.cpu 2.0 1150864248\npalm.cpu 0.5 1150864248\n\n
        #ok\npalm.cpu 2.0 1150864247\npalm.cpu 0.5 1150864248\neardrum.cpu 3.0 1150864250\n\n
        #[(timestamp1, metric_value1), (timestamp2, metric_value2), …]
        return self.convert_str_to_dict(response)

    def convert_str_to_dict(self, response):
        metric_dict = {}
        for substr in response.split("\n"):
            if substr == 'ok':
                pass
            elif substr != "":
                #print("substr =", substr)
                if len(substr.split(" ")) != 3:
                    raise ClientError
                metric, metric_value, timestamp = substr.split(" ")
                print("metric={} metric_value={} timestamp={}".format(metric, metric_value, timestamp))
                if metric_dict.get(metric) is None:
                    metric_dict[metric] = [(int(timestamp), float(metric_value))]
                else:
                    print("metric_dict.get({})={}".format(metric, metric_dict.get(metric)))
                    new_metric_tuple = (int(timestamp), float(metric_value))
                    print("new_metric_tuple = ", new_metric_tuple)
                    updated_metric_list = metric_dict.get(metric)
                    updated_metric_list.append(new_metric_tuple)
                    updated_metric_list.sort(key=lambda x: x[0])
                    print("updated_metric_list =", updated_metric_list)
                    metric_dict[metric] = updated_metric_list
                    #metric_dict[metric] = updated_metric_list.sort(key = lambda x : x[0])
        return metric_dict