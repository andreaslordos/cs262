import socket
from concurrent import futures


import grpc
import chat_pb2
import chat_pb2_grpc

host = '127.0.0.1'
port = 7976

class Greeter(chat_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        print("Received request: " + request.name)
        return chat_pb2.HelloReply(message='Hello, %s!' % request.name)

    def SayHelloAgain(self, request, context):
        print("Received request: " + request.name)
        return chat_pb2.HelloReply(message='Hello again, %s!' % request.name)

def serve():
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == '__main__':
    serve()