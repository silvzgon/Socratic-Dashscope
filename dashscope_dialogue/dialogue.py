import dashscope
from dashscope import Generation
from http import HTTPStatus
from flask import Flask, render_template, send_from_directory, request, jsonify, Response
from datetime import datetime
import json
import log
import pretreatment
import prompts

web = Flask(__name__)

dashscope.api_key = 'sk-2910abbb971e45df8718a46b2984bc56'

jsonFilePathOfHistory = './history/history.json'

maxTriesNumber = 3
maxCheckingNumber = 3

question = None
step = None
history = None
current = None
stepCount = None
descriptionCount = None
checkingCount = None

questionSent = {'message': 'none', 'time': datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")}
questionSentTime = datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
amendmentsSent = {'message': 'none', 'time': datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")}
amendmentsSentTime = datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
checkingSent = {'message': 'none', 'time': datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")}
checkingSentTime = datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
answerSent = {'message': 'none', 'time': datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")}
answerSentTime = datetime(1, 1, 1, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")


def agentCalling(prompt, history):
    response = Generation.call(
        model='sanle-v1',
        prompt=prompt,
        history=history
    )

    dialogue = None
    if response.status_code == HTTPStatus.OK:
        dialogue = {
            "user": prompt,
            "bot": response.output.text
        }
        return dialogue
    else:
        raise Exception('Error calling agent, code: {response.status_code}, status: {response.code}, message: {response.message}.')

def responseFormatting(prompt, history, expectedHeader, newHeader):
    flag = False

    for i in range(maxTriesNumber):
        dialogue = agentCalling(prompt, history)
        if dialogue["bot"].startswith(expectedHeader):
            dialogue["bot"] = newHeader + dialogue["bot"][len(expectedHeader):]
            current.append(dialogue["bot"])
            flag = True
            break
        else:
            log.logger.warning('[WARNING] Invaid response format, having made request again.')

    if flag:
        return dialogue
    else:
        raise Exception('Invalid response format.')

def stepDescribing(step):
    stepDescription = '-------------------------------------------------------------------------------------------------------\n'
    for i in range(len(step)):
        stepDescription += f'【步骤{i + 1}】\n'
        stepDescription += f'  提问：{step[i]["question"]}\n'
        stepDescription += f'  答案：{step[i]["answer"]}\n'
        stepDescription += ('  描述：1、' + step[i]["description"][0])
        for j in range(len(step[i]["description"])):
            if j:
                stepDescription += f'\n             {j + 1}、{step[i]["description"][j]}'
        stepDescription += '\n-------------------------------------------------------------------------------------------------------\n'
    return stepDescription

@web.route('/student')
def student():
    return render_template('student.html')

@web.route('/teacher')
def teacher():
    return render_template('teacher.html')

@web.route('/templates/<path:filename>')
def serve_temp_files(filename):
    return send_from_directory('templates', filename)

@web.route('/submitQuestion', methods=['POST'])
def submitQuestion():
    global question, step, history, current, stepCount, descriptionCount, checkingCount, questionSent
    stepCount = descriptionCount = checkingCount = 0

    try:
        with open(jsonFilePathOfHistory, 'r', encoding='utf-8') as file:
            history = json.load(file)
    except json.JSONDecodeError as e:
        history = []
        log.logger.warning(f"[WARNING] Fail when decode json, auto_initialized.")

    try:
        lineContent = request.json.get('lineContent')
        filePath = request.json.get('filePath')
        type = request.json.get('type')

        question, step = pretreatment.pretreatment(lineContent, filePath, '', type)
        current = [('【题目】' + question)]
        stepDescription = stepDescribing(step)

        prompt = prompts.firstRoundBeginning + ('#题目：' + step[stepCount]["question"] + '\n#对话：')
        dialogue = responseFormatting(prompt, [], '【老师】：', '')

        questionSent = {'message': 'completed', 'response': dialogue["bot"], 'question': lineContent, 'step': stepDescription, 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return jsonify({'message': 'completed', 'response': dialogue["bot"], 'question': lineContent})
    
    except Exception as e:
        log.logger.error(f'[ERROR] Fail in submit_question. {e}')
        questionSent = {'message': 'error', 'error': str(e), 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return jsonify({'message': 'error', 'error': str(e)})

def sendQuestion():
    global questionSent, questionSentTime

    if questionSent["time"] != questionSentTime:
        questionSentTime = questionSent["time"]
        message = json.dumps(questionSent)
        yield f"data: {message}\n\n"

@web.route('/receiveQuestion')
def receiveQuestion():
    return Response(sendQuestion(), content_type='text/event-stream')

@web.route('/submitAmendments', methods=['POST'])
def submitAmendments():
    global question, step, amendmentsSent

    try:
        lineContent = request.json.get('botResponse')
        amendments = request.json.get('userInput')

        _, step = pretreatment.pretreatment(lineContent, '', amendments, 'amendment')
        stepDescription = stepDescribing(step)

        prompt = prompts.firstRoundBeginning + ('#题目：' + step[stepCount]["question"] + '\n#对话：')
        dialogue = responseFormatting(prompt, [], '【老师】：', '')

        return jsonify({'message': 'completed', 'question': question, 'step': stepDescription, 'response': dialogue["bot"]})
    
    except Exception as e:
        log.logger.error(f'[ERROR] Fail in submit_amendments. {e}')
        amendmentsSent = {'message': 'error', 'error': str(e), 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return jsonify({'message': 'error', 'error': str(e)})

def sendAmendments():
    global amendmentsSent, amendmentsSentTime

    if amendmentsSent["time"] != amendmentsSentTime:
        amendmentsSentTime = amendmentsSent["time"]
        message = json.dumps(amendmentsSent)
        yield f"data: {message}\n\n"

@web.route('/receiveAmendments')
def receiveAmendments():
    return Response(sendAmendments(), content_type='text/event-stream')

@web.route('/submitChecking', methods=['POST'])
def submitChecking():
    global step, current, stepCount, checkingCount, checkingSent

    try:
        botResponse = '【老师】：' + str(request.json.get('botResponse'))
        userInput = str(request.json.get('userInput'))
        select = str(request.json.get('select'))

        if stepCount <= len(step):
            if checkingCount < maxCheckingNumber:
                checkingCount += 1
                if select == 'False':
                    current.append(botResponse)
                    checkingCount = maxCheckingNumber + 1
                    if stepCount < len(step):
                        checkingSent = {'message': 'completed', 'response': botResponse[5:], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'accepted'})
                    else:
                        stepCount += 1
                        checkingSent = {'message': 'end_completed', 'response': botResponse[5:], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'end_accepted'})
                else:
                    prompt = prompts.responseChecking + ('#初始语句：' + botResponse + '\n#修改意见：' + userInput + '\n#修改结果：')
                    dialogue = responseFormatting(prompt, [], '【老师】：', '')
                    return jsonify({'message': 'completed', 'response': dialogue["bot"], 'count': checkingCount, 'max': maxCheckingNumber})

            elif checkingCount == maxCheckingNumber:
                checkingCount += 1
                if select == 'False':
                    current.append(botResponse)
                    if stepCount < len(step):
                        checkingSent = {'message': 'completed', 'response': botResponse[5:], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'accepted'})
                    else:
                        stepCount += 1
                        checkingSent = {'message': 'end_completed', 'response': botResponse[5:], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'end_accepted'})
                else:
                    current.append(userInput)
                    if stepCount < len(step):
                        checkingSent = {'message': 'completed', 'response': userInput, 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'accepted'})
                    else:
                        stepCount += 1
                        checkingSent = {'message': 'end_completed', 'response': userInput, 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'end_accepted'})
                
            else:
                checkingCount += 1
                return jsonify({'message': 'invalid'})

        return jsonify({'message': 'end_invalid'})

    except Exception as e:
        log.logger.error(f'[ERROR] Fail in submit_checking. {e}')
        checkingSent = {'message': 'error', 'error': str(e), 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return jsonify({'message': 'error', 'error': str(e)})

def sendChecking():
    global checkingSent, checkingSentTime

    if checkingSent["time"] != checkingSentTime:
        checkingSentTime = checkingSent["time"]
        message = json.dumps(checkingSent)
        yield f"data: {message}\n\n"

@web.route('/receiveChecking')
def receiveChecking():
    return Response(sendChecking(), content_type='text/event-stream')

@web.route('/submitAnswer', methods=['POST'])
def submitAnswer():
    global step, history, current, stepCount, descriptionCount, checkingCount, maxCheckingNumber, answerSent
    checkingCount = 0

    try:
        if stepCount < len(step):
            userInput = request.json.get('userInput')
            current.append('【学生】' + userInput)
            
            prompt = prompts.answerChecking + ('#标准答案：' + step[stepCount]["answer"] + '\n#学生答案：' + userInput + '\n#判断：')
            dialogue = agentCalling(prompt, [])

            if "错误" in dialogue["bot"]:
                for i in range(len(step[stepCount]["description"])):
                    prompt = prompts.answerChecking + ('#标准答案：' + step[stepCount]["description"][i] + '\n#学生答案：' + userInput + '\n#判断：')
                    dialogue = agentCalling(prompt, [])
                    if "正确" in dialogue["bot"]: break

                if "错误" in dialogue["bot"]:
                    if descriptionCount >= len(step[stepCount]["description"]):
                        prompt = prompts.lastRoundIncorrect + ('#题目：' + step[stepCount]["question"] + '\n#正确答案：' + step[stepCount]["answer"] + '\n#学生答案：' + userInput + '\n#提示：')
                        dialogue1 = responseFormatting(prompt, [], '【老师】：', '')
                        current.append(dialogue1["bot"])
                        descriptionCount = 0
                        stepCount += 1
                        if stepCount < len(step):
                            prompt = prompts.middleRoundBeginning + ('#题目：' + step[stepCount]["question"] + '\n#对话：')
                            dialogue2 = responseFormatting(prompt, [], '【老师】：', '')
                            current.append(dialogue2["bot"])
                            answerSent = {'message': 'completed', 'response': dialogue1["bot"] + dialogue2["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            return jsonify({'message': 'completed', 'response': dialogue1["bot"] + dialogue2["bot"]})
                        else:
                            history.append(current)
                            with open(jsonFilePathOfHistory, 'w', encoding='utf-8') as file:
                                json.dump(history, file, ensure_ascii=False, indent=4)
                            answerSent = {'message': 'completed', 'response': dialogue1["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            return jsonify({'message': 'completed', 'response': dialogue1["bot"]})
                    
                    else:
                        prompt = prompts.middleRoundIncorrect + ('\n#题目：' + step[stepCount]["question"] + '\n#正确答案：' + step[stepCount]["answer"] + '\n#学生答案：' + userInput + '\n#描述：' + step[stepCount]["description"][descriptionCount] + '\n引导：')
                        dialogue = responseFormatting(prompt, [], '【老师】：', '')
                        current.append(dialogue["bot"])
                        descriptionCount += 1
                        answerSent = {'message': 'completed', 'response': dialogue["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        return jsonify({'message': 'completed', 'response': dialogue["bot"]})
                    
                else:
                    descriptionCount = i
                    prompt = prompts.middleRoundCorrect + ('#学生答案：' + userInput + '\n#回答：')
                    dialogue = responseFormatting(prompt, [], '【老师】：', '')
                    dialogue["bot"] += '你觉得接下来该怎么做呢？'
                    current.append(dialogue["bot"])
                    answerSent = {'message': 'completed', 'response': dialogue["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    return jsonify({'message': 'completed', 'response': dialogue["bot"]})
                
            else:
                prompt = prompts.lastRoundCorrect  + ('#答案：' + step[stepCount]["answer"] + '\n#回答：')
                dialogue1 = responseFormatting(prompt, [], '【老师】：', '')
                current.append(dialogue1["bot"])
                descriptionCount = 0
                stepCount += 1
                if stepCount < len(step):
                    prompt = prompts.middleRoundBeginning + ('#题目：' + step[stepCount]["question"] + '\n#对话：')
                    dialogue2 = responseFormatting(prompt, [], '【老师】：', '')
                    current.append(dialogue2["bot"])
                    answerSent = {'message': 'completed', 'response': dialogue1["bot"] + dialogue2["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    return jsonify({'message': 'completed', 'response': dialogue1["bot"] + dialogue2["bot"]})
                else:
                    history.append(current)
                    with open(jsonFilePathOfHistory, 'w', encoding='utf-8') as file:
                        json.dump(history, file, ensure_ascii=False, indent=4)
                    answerSent = {'message': 'completed', 'response': dialogue1["bot"], 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    return jsonify({'message': 'completed', 'response': dialogue1["bot"]})

        stepCount += 1
        return jsonify({'message': 'invalid'})
    
    except Exception as e:
        log.logger.error(f'[ERROR] Fail in submit_answer. {e}')
        answerSent = {'message': 'error', 'error': str(e), 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return jsonify({'message': 'error', 'error': str(e)})

def sendAnswer():
    global answerSent, answerSentTime

    if answerSent["time"] != answerSentTime:
        answerSentTime = answerSent["time"]
        message = json.dumps(answerSent)
        yield f"data: {message}\n\n"

@web.route('/receiveAnswer')
def receiveAnswer():
    return Response(sendAnswer(), content_type='text/event-stream')

if __name__ == '__main__':
    # http://127.0.0.1:5000/student
    # http://127.0.0.1:5000/teacher
    web.run(debug=True)