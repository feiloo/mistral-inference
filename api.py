import zmq
import argparse
import logging
from time import time
from mistral_inference.main import get_api

# api = Api('', instruct=True)
# msgs = []
# answer, msgs = api('a', msgs)
# return api

class Server:
    def __init__(self):
        self.context = zmq.Context()
        self.responder = self.context.socket(zmq.REP)
        self.responder.bind("tcp://*:5555")

        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        #handler = logging.FileHandler("server.log")
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.info(f"Initializing model")
        self.api = get_api()
        self.logger.info(f"API ready")
        self.msgs = []

    def start(self):
        while 1:
            request = self.responder.recv_string()
            self.logger.info(f"Received request: {request}")
            if request.strip() == 'quit':
                self.responder.send_string('has quitted')
                break
            elif request.strip() == 'clear':
                self.msgs = []
                self.responder.send_string('cleared')
                continue

            self.logger.info(f"Calling with msgs: {self.msgs}")
            reply, msgs_ = self.api(str(request), self.msgs, max_tokens=1024)
            self.msgs += msgs_

            self.responder.send_string(reply)

class Client:
    def __init__(self):
        self.context = zmq.Context()
        self.requester = self.context.socket(zmq.REQ)
        self.requester.connect("tcp://localhost:5555")

    def send_request(self, request):
        self.requester.send_string(request)
        reply = self.requester.recv_string()
        return reply

#- by codestral-mamba-7b-0.1
def multiline_input(prompt, max_lines):
    print(prompt, end='')

    lines = []
    for i in range(max_lines):
        try:
            line = input()
            lines.append(line)
        except EOFError:
            break

    text = '\n'.join(lines)
    return text
#-#

import json
from uuid import uuid4
from datetime import datetime
session = uuid4()
convodb = f'convodb_2_{session}.jsonl'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='inference api')
    #parser.add_argument('mode', choices=['server', 'client', 'repl'], help='the mode to run the program in')
    subparsers = parser.add_subparsers(dest='mode')
    server_parser = subparsers.add_parser('server', help='run server')
    client_parser = subparsers.add_parser('prompt', help='make single prompt')
    client_parser.add_argument('prompt_text', help='the prompt to query the ai with')
    repl_parser = subparsers.add_parser('repl', help='multiple prompts in a repl-fashion')
    args = parser.parse_args()

    if args.mode == "server":
        server = Server()
        server.start()
    elif args.mode == "client":
        client = Client()
        reply = client.send_request('clear')
        reply = client.send_request(str(args.prompt))
        print(f'ai: {reply}')
    elif args.mode == "repl":
        client = Client()
        client.send_request('clear')
        thread_id = str(uuid4())
        while 1:
            try:
                print('====')
                prompt = multiline_input('> ', 512)

                with open(convodb, 'a') as f:
                    f.write(json.dumps({'user_input':prompt, 'thread_id':thread_id, 'date':str(datetime.now().isoformat())})+'\n')

                if prompt.strip() == 'clear':
                    reply = client.send_request('clear')
                else:
                    reply = client.send_request(str(prompt))

                print('----')
                print(reply)
                with open(convodb, 'a') as f:
                    f.write(json.dumps({'codestral-mamba-7b_answer':reply, 'thread_id':thread_id, 'date':str(datetime.now().isoformat())})+'\n')

                if prompt.strip() == 'clear':
                    thread_id = str(uuid4())

            except KeyboardInterrupt:
                break
