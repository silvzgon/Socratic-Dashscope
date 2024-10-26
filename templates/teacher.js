const receiveQuestion = new EventSource('/receiveQuestion');
let receiveQuestionMessage = {};
receiveQuestion.onmessage = function(event) {
    receiveQuestionMessage = JSON.parse(event.data);
    removeFromDialogue("stepBox", 0);
    if (receiveQuestionMessage.message == "completed") {
        appendToDialogue("stepBox", "【题目】" + receiveQuestionMessage.question + "\n\n" + receiveQuestionMessage.step, "systemText");
        document.getElementById("amendments").placeholder = "你的修改意见...";
        document.getElementById("amendments").disabled = false;
        document.getElementById("amendmentsSelect").disabled = false;
        document.getElementById("amendmentsSubmit").disabled = false;
    } else if (receiveQuestionMessage.message == "error") {
        console.error('error from student: ' + receiveQuestionMessage.error);
        appendToDialogue("stepBox", "【系统】程序错误，正在退出...", "systemText");
        document.getElementById("amendments").placeholder = "程序错误，无法输入。";
    }
};

const receiveAnswer = new EventSource('/receiveAnswer');
let receiveAnswerMessage = {};
receiveAnswer.onmessage = function(event) {
    receiveAnswerMessage = JSON.parse(event.data);
    if (receiveAnswerMessage.message == "completed") {
        removeFromDialogue("dialogueBox", 1);
        appendToDialogueWithIcon("dialogueBox", receiveAnswerMessage.response, "botText", "templates/sanle.png", "left");
        document.getElementById("checking").placeholder = "你的修改意见...";
        document.getElementById("checking").disabled = false;
        document.getElementById("checkingSelect").disabled = false;
        document.getElementById("checkingSubmit").disabled = false;
    } else if (receiveAnswerMessage.message == "error") {
        console.error('error from student: ' + receiveAnswerMessage.error);
        removeFromDialogue("dialogueBox", 0);
        appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
        document.getElementById("checking").placeholder = "程序错误，无法输入。";
    }
};

function toggleInput(elementId, selectId) {
    const fileInputDiv = document.getElementById(elementId);
    const type = document.getElementById(selectId).value;
    if (type === "True") {
        fileInputDiv.style.display = "block";
    } else {
        fileInputDiv.style.display = "none";
    }
}

function toggleOption(selectedOptionId) {
    const option1 = document.getElementById('step');
    const option2 = document.getElementById('dialogue');

    if (selectedOptionId === 'step') {
        option1.classList.add('selected');
        option2.classList.remove('selected');
        document.getElementById("stepBox").style.display = "block"
        document.getElementById("dialogueBox").style.display = "none"
    } else {
        option2.classList.add('selected');
        option1.classList.remove('selected');
        document.getElementById("dialogueBox").style.display = "block"
        document.getElementById("stepBox").style.display = "none"
    }
}

function appendToDialogue(elementId, textContent, className) {
    const dialogueBox = document.getElementById(elementId);
    const p = document.createElement("p");
    p.textContent = textContent;
    p.className = className;
    dialogueBox.appendChild(p);
    dialogueBox.scrollTop = dialogueBox.scrollHeight;
}

function appendToDialogueWithIcon(elementId, textContent, className, imgSrc, align) {
    const dialogueBox = document.getElementById(elementId);
    
    const div = document.createElement("div");
    div.style.display = "flex";
    div.style.alignItems = "center";
    div.style.marginBottom = "20px";

    if (align === "right") {
        div.style.flexDirection = "row-reverse";
    }

    const img = document.createElement("img");
    img.src = imgSrc;
    img.alt = "Speaker";
    img.style.width = "20px";
    img.style.height = "20px";
    img.style.margin = align === "left" ? "0 10px 0 0" : "0 0 0 10px";

    const p = document.createElement("p");
    p.textContent = textContent;
    p.className = className;
    p.style.margin = "0";
    
    p.style.border = "1px solid #ddd";
    p.style.borderRadius = "8px";
    p.style.padding = "10px";
    p.style.backgroundColor = "#f4f7f6";
    p.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";

    div.appendChild(img);
    div.appendChild(p);

    dialogueBox.appendChild(div);
    dialogueBox.scrollTop = dialogueBox.scrollHeight;
}

function removeFromDialogue(elementId, index) {
    const dialogueBox = document.getElementById(elementId);
    while (dialogueBox.children.length > index) {
        dialogueBox.removeChild(dialogueBox.lastChild);
    }
}

document.getElementById("stepForm").onsubmit = function(event) {
    event.preventDefault();

    const select = document.getElementById("amendmentsSelect").value;

    if (select == "True") {
        const botResponse = document.getElementById("stepBox").lastChild.textContent;
        const userInput = document.getElementById("amendments").value;
        document.getElementById("amendments").value = ""

        document.getElementById("amendments").placeholder = "请勿输入，步骤生成中...";
        document.getElementById("amendments").disabled = true;
        document.getElementById("amendmentsSelect").disabled = true;
        document.getElementById("amendmentsSubmit").disabled = true;

        fetch("/submitAmendments", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ botResponse: botResponse, userInput: userInput }),
        })
        .then(response => response.json())
        .then(data => {
            removeFromDialogue("stepBox", 0);
            if (data.message == "completed") {
                appendToDialogue("stepBox", "【题目】" + data.question + "\n\n" + data.step, "systemText");
                document.getElementById("amendments").placeholder = "你的修改意见...";
                document.getElementById("amendments").disabled = false;
                document.getElementById("amendmentsSelect").disabled = false;
                document.getElementById("amendmentsSubmit").disabled = false;
                receiveQuestionMessage.response = data.response;
            } else if (data.message == "error") {
                console.error('error: ' + data.error);
                appendToDialogue("stepBox", "【系统】程序错误，正在退出...", "systemText");
                document.getElementById("amendments").placeholder = "程序错误，无法输入。";
            }
        });

    } else {
        document.getElementById("dialogue").classList.remove('disabled');
        document.getElementById("dialogue").classList.add('selected');
        document.getElementById("step").classList.remove('selected');
        document.getElementById("dialogueForm").style.display = "block";
        document.getElementById("stepForm").style.display = "none";
        document.getElementById("stepBox").style.display = "none";

        appendToDialogue("dialogueBox", "【题目】" + receiveQuestionMessage.question, "systemText");
        appendToDialogueWithIcon("dialogueBox", receiveQuestionMessage.response, "botText", "templates/sanle.png", "left");
    }
}

document.getElementById("dialogueForm").onsubmit = function(event) {
    event.preventDefault();

    const botResponse = document.getElementById("dialogueBox").lastChild.textContent;
    const userInput = document.getElementById("checking").value;
    const select = document.getElementById("checkingSelect").value;
    document.getElementById("checking").value = "";

    if (select == "True") {
        appendToDialogueWithIcon("dialogueBox", userInput, "userText", "templates/teacher.png", "right");
    } else {
        appendToDialogueWithIcon("dialogueBox", "通过。", "userText", "templates/teacher.png", "right");
    }

    document.getElementById("checking").placeholder = "请勿输入，回答生成中...";
    document.getElementById("checking").disabled = true;
    document.getElementById("checkingSelect").disabled = true;
    document.getElementById("checkingSubmit").disabled = true;

    fetch("/submitChecking", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ botResponse: botResponse, userInput: userInput, select: select }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message == "completed") {
            document.getElementById("checking").placeholder = "你的修改意见...";
            document.getElementById("checking").disabled = false;
            document.getElementById("checkingSelect").disabled = false;
            document.getElementById("checkingSubmit").disabled = false;
            if (data.count == data.max) {
                appendToDialogue("dialogueBox", "【系统】最后一次尝试修改，如果本次修改结果未通过，请直接输入你的修改结果。", "systemText");
            }
            appendToDialogueWithIcon("dialogueBox", data.response, "botText", "templates/sanle.png", "left");
        } else if (data.message == "accepted") {
            document.getElementById("checking").placeholder = "请勿输入，学生回答中...";
            document.getElementById("checking").disabled = true;
            appendToDialogue("dialogueBox", "【系统】修改已执行，等待学生回答...", "systemText");
        } else if (data.message == "end_accepted") {
            document.getElementById("checking").placeholder = "程序结束，请勿输入。";
            document.getElementById("checking").disabled = true;
            appendToDialogue("dialogueBox", "【系统】修改完成，数据已写入，正在退出程序...", "systemText");
        } else if (data.message == "invalid") {
            document.getElementById("checking").placeholder = "修改结束，请勿输入。";
            document.getElementById("checking").disabled = true;
            appendToDialogue("dialogueBox", "【系统】无效输入，修改已完成。", "systemText");
        } else if (data.message == "end_invalid") {
            document.getElementById("checking").placeholder = "程序结束，请勿输入。";
            document.getElementById("checking").disabled = true;
            appendToDialogue("dialogueBox", "【系统】无效输入，程序已结束。", "systemText");
        } else if (data.message == "error") {
            console.error('error: ' + data.error);
            document.getElementById("checking").placeholder = "程序错误，请勿输入。";
            document.getElementById("checking").disabled = true;
            appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
        }
    });
}