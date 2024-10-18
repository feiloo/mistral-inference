from src.mistral_inference.main import get_api

from mistral_common.protocol.instruct.tool_calls import Function, Tool
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from mistral_common.protocol.instruct.messages import AssistantMessage, UserMessage
from mistral_common.protocol.instruct.tool_calls import *

tools=[
    Tool(
        function=Function(
            name="get_current_weather",
            description="Get the current weather",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use. Infer this from the users location.",
                    },
                },
                "required": ["location", "format"],
            },
        )
    )
]

tools = []

#- by codestral-mamba-7b-0.1
def multiline_input(prompt, max_lines):
    print(prompt)

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

api = get_api()
msgs = []

#answer, msgs = api(user_input, msgs, tools=tools)
class Context:
    def __init__(self):
        self.msgs = []

    def add(self, msg):
        self.msgs.append(msg)



def subprompt(answer, n):
    if n == 0:
        return answer
    else:
        nextprompt = prompt.replace("$ANSWER", f' {answer} ', 1)
        print(nextprompt)
        answer, msgs = api(nextprompt, [])
        print(answer)
        return subprompt(answer, n-1)


ctx = Context()
while 1:
    print('====')
    prompt = multiline_input('> ', 200)
    print('----')
    if prompt.strip() in ['new thread', 'nt']:
        ctx = Context()
        print('----}')
        print('New Thread')
        print('{----')
        continue

    if '$ANSWER' in prompt:
        answer, msgs = api(prompt, ctx.msgs)
        subprompt(answer, 3)
        ctx.add(msgs[-1])
    else:
        answer, msgs = api(prompt, ctx.msgs)
        ctx.add(msgs[-1])

    print(answer)
