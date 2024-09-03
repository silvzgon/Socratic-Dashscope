from openai import OpenAI
import time
import json
import log
import prompts

jsonFilePathOfStep = './temp/step.json'

maxTriesNumber = 3

def pretreatment(lineContent, filePath, amendments, type):
    i = 0

    while (1):
        try:
            i += 1

            client = OpenAI(api_key="# your openai api key here")

            if type == 'True':
                file = client.files.create(
                    file = open(filePath, "rb"),
                    purpose = 'assistants'
                )
                assistant = client.beta.assistants.create(
                    instructions = "You are a personal tutor. When asked a math question, write and run code to answer the question.",
                    model = "gpt-4o",
                    tools = [{"type": "code_interpreter"}],
                    tool_resources = {
                        "code_interpreter": {
                            "file_ids": [file.id]
                        }}
                )
                thread = client.beta.threads.create(
                    messages = [{
                            "role": "user",
                            "content": ('请你根据给出的题目以及给出的文件中的数据，' + prompts.stepsGetting + lineContent),
                        }]
                )

            elif type == 'False':
                assistant = client.beta.assistants.create(
                    instructions = "You are a personal tutor. When asked a math question, write and run code to answer the question.",
                    model = "gpt-4o",
                    tools = [{"type": "code_interpreter"}],
                )
                thread = client.beta.threads.create(
                    messages = [{
                            "role": "user",
                            "content": ('请你根据给出的题目，' + prompts.stepsGetting + lineContent),
                        }]
                )

            else:
                assistant = client.beta.assistants.create(
                    instructions = "You are a personal tutor. When asked a math question, write and run code to answer the question.",
                    model = "gpt-4o",
                    tools = [{"type": "code_interpreter"}],
                )
                thread = client.beta.threads.create(
                    messages = [{
                            "role": "user",
                            "content": ('请你根据给出的题目，' + prompts.stepRemediating + lineContent + amendments),
                        }]
                )

            run = client.beta.threads.runs.create(
                thread_id = thread.id,
                assistant_id = assistant.id
            )

            while (1):
                time.sleep(0.1)
                run = client.beta.threads.runs.retrieve(
                    thread_id = thread.id,
                    run_id = run.id
                )
                if run.status == 'completed':
                    break

            messages = client.beta.threads.messages.list(
                thread_id = thread.id
            )

            json_file = client.files.content(messages.data[0].content[0].text.annotations[0].file_path.file_id)
            json_data = json_file.read()

            with open(jsonFilePathOfStep, "wb") as file:
                file.write(json_data)

            with open(jsonFilePathOfStep, 'r', encoding='utf-8') as file:
                step = file.read()
                step = json.loads(step)

            return lineContent, step
        
        except Exception as e:
            if i < maxTriesNumber:
                log.logger.warning('[WARNING] No json file generated.')
            else:
                raise Exception(f'Fail when solving question: {e}')
