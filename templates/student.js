const receiveAmendments = new EventSource('/receiveAmendments');
let receiveAmendmentsMessage = {};
receiveAmendments.onmessage = function(event) {
    receiveAmendmentsMessage = JSON.parse(event.data);
    if (receiveAmendmentsMessage.message == "error") {
        console.error("error from teacher: " + receiveAmendmentsMessage.error);
        document.getElementById("userInput").placeholder = "程序错误，请勿输入。";
        document.getElementById("userInput").disabled = true;
        document.getElementById("submitAnswer").disabled = true;
        appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
    }
};

const receiveChecking = new EventSource('/receiveChecking');
let receiveCheckingMessage = {};
receiveChecking.onmessage = function(event) {
    receiveCheckingMessage = JSON.parse(event.data);
    if (receiveCheckingMessage.message == "completed") {
        document.getElementById("userInput").placeholder = "你的回答...";
        document.getElementById("userInput").disabled = false;
        document.getElementById("submitAnswer").disabled = false;
        appendToDialogueWithIcon("dialogueBox", receiveCheckingMessage.response, "botText", "templates/sanle.png", "left");
    } else if (receiveCheckingMessage.message == "end_completed") {
        document.getElementById("userInput").placeholder = "程序结束，请勿输入。";
        document.getElementById("userInput").disabled = true;
        document.getElementById("submitAnswer").disabled = true;
        appendToDialogueWithIcon("dialogueBox", receiveCheckingMessage.response, "botText", "templates/sanle.png", "left");
        appendToDialogue("dialogueBox", "【系统】对话完成，数据已写入，正在退出程序...", "systemText");
    } else if (receiveCheckingMessage.message == "error") {
        console.error("error from teacher: " + receiveCheckingMessage.error);
        document.getElementById("userInput").placeholder = "程序错误，请勿输入。";
        document.getElementById("userInput").disabled = true;
        document.getElementById("submitAnswer").disabled = true;
        appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
    }
};

function toggleFileInput() {
    const fileInputDiv = document.getElementById("filePathInputDiv");
    const type = document.getElementById("type").value;
    if (type === "True") {
        fileInputDiv.style.display = "block";
    } else {
        fileInputDiv.style.display = "none";
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

document.getElementById("initialForm").onsubmit = function(event) {
    event.preventDefault();

    const lineContent = document.getElementById("lineContent").value;
    const filePath = document.getElementById("filePath").value;
    const type = document.getElementById("type").value;

    document.getElementById("loading").style.visibility = "visible";
    document.getElementById("lineContent").disabled = true;
    document.getElementById("filePath").disabled = true;
    document.getElementById("type").disabled = true;
    document.getElementById("submitQuestion").disabled = true;

    fetch("/submitQuestion", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ lineContent: lineContent, type: type, filePath: filePath }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("dialoguePage").style.display = "block";
        document.getElementById("initialPage").style.display = "none";

        if (data.message == "completed") {
            document.getElementById("userInput").placeholder = "请勿输入，教师检查中...";
            appendToDialogue("dialogueBox", "【题目】" + data.question, "systemText");
        } else if (data.message == "error") {
            console.error("error: " + data.error);
            document.getElementById("userInput").placeholder = "程序错误，请勿输入。";
            appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
        }
    });
}

document.getElementById("dialogueForm").onsubmit = function(event) {
    event.preventDefault();

    const userInput = document.getElementById("userInput").value;
    document.getElementById("userInput").value = "";
    appendToDialogueWithIcon("dialogueBox", userInput, "userText", "templates/student.png", "right");
    document.getElementById("userInput").placeholder = "请勿输入，回答生成中...";
    document.getElementById("userInput").disabled = true;
    document.getElementById("submitAnswer").disabled = true;

    fetch("/submitAnswer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ userInput: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message == "completed") {
            document.getElementById("userInput").placeholder = "请勿输入，教师检查中...";
        } else if (data.message == "invalid") {
            appendToDialogue("dialogueBox", "【系统】无效输入，程序已结束。", "systemText");
        } else if (data.message == "error") {
            console.error('error: ' + data.error);
            appendToDialogue("dialogueBox", "【系统】程序错误，正在退出...", "systemText");
        }
    });
}