import socket
import asyncio


def run_server(host, port):
    metric_server = MetricServer()
    loop = asyncio.get_event_loop()
    coro = loop.create_server(
        ClientServerProtocol,
        host, port
    )

    server = loop.run_until_complete(coro)
    print("Server started on {}:{}".format(host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


class MetricServer():

    metric_dict = {}

    @staticmethod
    def process_data(data):
        print("Data to process:", data)
        processed_data = None
        if data.startswith("get ") and data.endswith("\n"):
            processed_data = MetricServer.process_get(data)
        elif data.startswith("put ") and data.endswith("\n"):
            processed_data = MetricServer.process_put(data)
            print("metric_dict after PUT:", MetricServer.metric_dict)
        else:
            processed_data = MetricServer.error_response("wrong command")
        return processed_data

    @staticmethod
    def convert_metric_to_string(metric):
        #ok\npalm.cpu 2.0 1150864248\npalm.cpu 0.5 1150864248\n\n
        result = ""
        if MetricServer.metric_dict.get(metric) is None:
            return ""
        else:
            values = MetricServer.metric_dict.get(metric)
            print("values:", values)
            for x in values:
                result += "{} {} {}\n".format(metric, x[1], x[0])
            print("Result string after extracting key:", result)
        return result

    @staticmethod
    def process_get(data):
        try:
            #get palm.cpu\n
            #get *\n
            print("Processing GET data:", data)
            processed_data = None
            data = data.replace("\n", "")
            _, metric = data.split(" ")
            print("Trying to get metric: ", metric)
            if metric != "*":
                processed_data = MetricServer.convert_metric_to_string(metric)
            else:
                processed_data = ""
                for key in MetricServer.metric_dict:
                    print("Processing key: ", key)
                    processed_data += MetricServer.convert_metric_to_string(key)
            return MetricServer.ok_response(processed_data)
        except ValueError as err:
            return MetricServer.error_response("wrong command")

    @staticmethod
    def process_put(data):
        try:
            # put palm.cpu 23.7 1150864247\n
            print("Processing PUT data:", data)
            processed_data = None
            data = data.replace("\n", "")
            _, metric, metric_value, timestamp = data.split(" ")
            if MetricServer.metric_dict.get(metric) is None:
                MetricServer.metric_dict[metric] = [(int(timestamp), float(metric_value))]
            else:
                values = MetricServer.metric_dict.get(metric)
                print("metric_dict.put({})={}".format(metric, MetricServer.metric_dict.get(metric)))
                new_metric_tuple = (int(timestamp), float(metric_value))
                print("new_metric_tuple = ", new_metric_tuple)
                updated_metric_list = MetricServer.metric_dict.get(metric)
                for x in updated_metric_list:
                    if x[0] == int(timestamp):
                        updated_metric_list.remove(x)
                updated_metric_list.append(new_metric_tuple)
                updated_metric_list.sort(key=lambda x: x[0])
                print("updated_metric_list =", updated_metric_list)
                MetricServer.metric_dict[metric] = updated_metric_list
                # metric_dict[metric] = updated_metric_list.sort(key = lambda x : x[0])
            print(MetricServer.metric_dict)
            return MetricServer.ok_response()
        except ValueError as err:
            return MetricServer.error_response("wrong command")

    def ok_response(data=None):
        if data is None:
            response = "ok\n\n"
        elif data == "":
            response = "ok\n\n"
        else:
            response = "ok\n" + data + "\n"
        return response

    def error_response(data=None):
        if data is None:
            response = "error\n\n"
        elif data == "":
            response = "error\n\n"
        else:
            response = "error\n" + data + "\n\n"
        return response


class ClientServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        print("Connection established", transport.get_extra_info('socket'))

    def data_received(self, data):
        decoded_data = data.decode()
        print("Data received:", decoded_data)
        #print("type(decoded_data) =", type(decoded_data))
        resp = MetricServer.process_data(decoded_data)
        print("Server response:", resp)
        self.transport.write(resp.encode())


