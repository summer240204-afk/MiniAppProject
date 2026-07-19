const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

if (tg) {
    tg.ready();
    tg.expand();
}

const choiceScreen = document.getElementById("choiceScreen");
const summaryScreen = document.getElementById("summaryScreen");

const backBtn = document.getElementById("backBtn");
const sendBtn = document.getElementById("sendBtn");
const waitingBtn = document.getElementById("waitingBtn");

const summaryIcon = document.getElementById("summaryIcon");
const summaryTitle = document.getElementById("summaryTitle");
const summaryMeaning = document.getElementById("summaryMeaning");
const summaryView = document.getElementById("summaryView");
const summaryExample = document.getElementById("summaryExample");
const typingStatus = document.getElementById("typingStatus");
const exampleName = document.getElementById("exampleName");

const phonePreview = document.getElementById("phonePreview");
const defaultExample = document.getElementById("defaultExample");
const pushTitle = document.getElementById("pushTitle");
const pushText = document.getElementById("pushText");

const successOverlay = document.getElementById("successOverlay");
const successMessage = document.getElementById("successMessage");

let selectedAction = null;
let typingAnimationTimer = null;

const actions = {
    chatNick: {
        title: "Ник активного чата",
        icon: "👀",
        type: "default",
        meaning: "Функция, которая показывает снизу под именем пользователя ник того, с кем он прямо сейчас находится в чате.",
        view: "Это выглядит как плашка сверху: «Сейчас в чате с @username».",
        example: "Сейчас в чате с @username."
    },

    chatActions: {
        title: "Действия в чате",
        icon: "💬",
        type: "push",
        meaning: "Функция отправляет пуш-уведомления сверху экранна, чтобы вы сразу видели важные действия собеседника в вашем личном чате.",
        view: "В уведомлениях будут отображаться действия собеседника: пересылка сообщений из вашего чата, вход в личный чат, блокировка/разблокировка, скриншот переписки и т.п.",
        example: "Сделал(-а) скриншот вашей переписки",
        pushTitle: "Пользователь",
        pushText: "Сделал(-а) скриншот вашей переписки"
    },

    liveTyping: {
        title: "Живой набор текста",
        icon: "⌨️",
        type: "typing",
        meaning: "Функция, где видно как человек набирает и стирает текст в вашем чате у себя на телефоне в реальном времени.",
        view: "Например, под статусом «печатает…» появляется строка с изменяющимся текстом.",
        example: "прив... привет... нет, удалил"
    }
};

function getFinalMessage() {
    if (!selectedAction) {
        return "";
    }

    return (
        "✅ Запрос принят!\n\n\n" +
        "Выбранный раздел: " + selectedAction.title + "\n\n\n" +
        "⏳ Ожидание обработки: 48–56 часов\n\n" +
        "Бот пришлет сообщение после проверки🙏🏼\n\n" +
        "Пожалуйста, не отписывайтесь от спонсоров до завершения проверки"
    );
}

function stopTypingAnimation() {
    if (typingAnimationTimer) {
        clearTimeout(typingAnimationTimer);
        typingAnimationTimer = null;
    }
}

function resetPreviewState() {
    phonePreview.classList.remove("active");
    defaultExample.classList.remove("hidden");
    defaultExample.classList.remove("typing-demo");
    typingStatus.style.display = "none";
}

function showDefaultPreview(exampleText) {
    phonePreview.classList.remove("active");
    defaultExample.classList.remove("hidden");
    defaultExample.classList.remove("typing-demo");
    typingStatus.style.display = "none";
    summaryExample.textContent = exampleText || "";
}

function showPushPreview(title, text) {
    phonePreview.classList.add("active");
    defaultExample.classList.add("hidden");
    defaultExample.classList.remove("typing-demo");
    typingStatus.style.display = "none";

    pushTitle.textContent = title;
    pushText.textContent = text;
}

function startTypingAnimation() {
    stopTypingAnimation();

    const phrases = [
        "прив",
        "привет",
        "привет, я хотел",
        "привет, я хотел сказать",
        "привет, я хотел сказать тебе",
        "привет, я хотел",
        "привет",
        "",
        "нет",
        "нет, удалил",
        "",
        "ладно",
        "ладно, потом",
        "ладно, потом напишу",
        ""
    ];

    let phraseIndex = 0;
    let charIndex = 0;
    let currentText = "";
    let mode = "typing";

    function animate() {
        const targetText = phrases[phraseIndex];

        if (mode === "typing") {
            currentText = targetText.slice(0, charIndex);
            summaryExample.textContent = currentText || "";

            charIndex++;

            if (charIndex > targetText.length) {
                mode = "pause";
                typingAnimationTimer = setTimeout(animate, 650);
                return;
            }

            typingAnimationTimer = setTimeout(animate, 80);
            return;
        }

        if (mode === "pause") {
            mode = "deleting";
            typingAnimationTimer = setTimeout(animate, 250);
            return;
        }

        if (mode === "deleting") {
            currentText = currentText.slice(0, -1);
            summaryExample.textContent = currentText || "";

            if (currentText.length === 0) {
                phraseIndex = (phraseIndex + 1) % phrases.length;
                charIndex = 0;
                mode = "typing";

                typingAnimationTimer = setTimeout(animate, 350);
                return;
            }

            typingAnimationTimer = setTimeout(animate, 45);
        }
    }

    animate();
}

document.querySelectorAll(".action-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const key = button.dataset.key;
        selectedAction = actions[key];

        if (!selectedAction) {
            console.error("Не найден раздел для кнопки:", key);
            return;
        }

        stopTypingAnimation();
        resetPreviewState();

        summaryIcon.textContent = selectedAction.icon;
        summaryTitle.textContent = selectedAction.title;
        summaryMeaning.textContent = selectedAction.meaning;
        summaryView.textContent = selectedAction.view;
        summaryExample.textContent = selectedAction.example;

        if (selectedAction.type === "push") {
            showPushPreview(selectedAction.pushTitle, selectedAction.pushText);
        } else if (selectedAction.type === "typing") {
            showDefaultPreview(selectedAction.example);
            defaultExample.classList.add("typing-demo");
            typingStatus.style.display = "block";
            startTypingAnimation();
        } else {
            showDefaultPreview(selectedAction.example);
        }

        choiceScreen.classList.add("hidden");
        summaryScreen.classList.remove("hidden");
    });
});

backBtn.addEventListener("click", () => {
    stopTypingAnimation();

    summaryScreen.classList.add("hidden");
    choiceScreen.classList.remove("hidden");
});

sendBtn.addEventListener("click", () => {
    if (!selectedAction) {
        return;
    }

    const finalMessage = getFinalMessage();

    if (successMessage) {
        successMessage.textContent = finalMessage;
    }

    if (successOverlay) {
        successOverlay.classList.remove("hidden");
    } else if (tg) {
        tg.showAlert(finalMessage);
    } else {
        alert(finalMessage);
    }
});

waitingBtn.addEventListener("click", () => {
    try {
        stopTypingAnimation();

        if (tg) {
            tg.close();
        } else {
            window.close();
        }
    } catch (error) {
        console.error("Ошибка закрытия Mini App:", error);
        window.close();
    }
});