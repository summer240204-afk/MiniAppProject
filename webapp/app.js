const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const choiceScreen = document.getElementById("choiceScreen");
const summaryScreen = document.getElementById("summaryScreen");

const backBtn = document.getElementById("backBtn");
const sendBtn = document.getElementById("sendBtn");

const summaryIcon = document.getElementById("summaryIcon");
const summaryTitle = document.getElementById("summaryTitle");
const summaryMeaning = document.getElementById("summaryMeaning");
const summaryView = document.getElementById("summaryView");
const summaryExample = document.getElementById("summaryExample");
const typingStatus = document.getElementById("typingStatus");
let typingAnimationTimer = null;
const phonePreview = document.getElementById("phonePreview");
const defaultExample = document.getElementById("defaultExample");
const pushTitle = document.getElementById("pushTitle");
const pushText = document.getElementById("pushText");

let selectedAction = null;

const actions = {
    chatNick: {
        title: "Ник активного чата",
        icon: "👀",
        type: "default",
        meaning: "Функция, которая показывает снизу над именем пользователя ник того, с кем он прямо сейчас находится в чате",
        view: "Примерно это выглядит как плашка сверху: «Сейчас в чате с @username».",
        example: "сейчас в чате с @best_friend"
    },

    chatEnter: {
        title: "Вход в ваш чат",
        icon: "🚪",
        type: "push",
        meaning: "Функция, где отправляется Пуш-уведомление сверху экрана, что пользователь открыл переписку именно с вами.",
        view: "Например, сверху экрана телефона появляется Пуш-уведомление: «@username зашёл в ваш чат».",
         example: "@username зашёл в ваш чат",
        pushTitle: "Вход в ваш чат",
        pushText: "@username только что открыл переписку с вами"
    },

    deletedMessage: {
    title: "Удалённое сообщение",
    icon: "🗑️",
    type: "push",
    meaning: "Функция, которая отправляет Пуш-уведомление сверху экрана, если пользователь написал сообщение, а потом удалил его для двоих.",
    view: "Пример плашки: «@username удалил сообщение для двоих: “ладно, забудь…”».",
    example: "@username удалил: «ладно, забудь…»",
    pushTitle: "Удалённое сообщение",
    pushText: "@username удалил сообщение для двоих: «ладно, забудь…»"
},

    liveTyping: {
        title: "Живой набор текста",
        icon: "⌨️",
        type: "typing",
        meaning: "Функция, где видно, как человек набирает и стирает текст у себя на телефоне.",
        view: "Например, под статусом «печатает…» появляется строка с изменяющимся текстом: «прив…», «привет, я…», «нет, не буду писать».",
        example: "прив... привет... нет, удалил"
    }
};
function stopTypingAnimation() {
    if (typingAnimationTimer) {
        clearTimeout(typingAnimationTimer);
        typingAnimationTimer = null;
    }
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
        "",
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
        if (selectedAction.type === "typing") {
    defaultExample.classList.add("typing-demo");
    typingStatus.style.display = "block";
} else {
    defaultExample.classList.remove("typing-demo");
    typingStatus.style.display = "none";
}

        stopTypingAnimation();

        summaryIcon.textContent = selectedAction.icon;
        summaryTitle.textContent = selectedAction.title;
        summaryMeaning.textContent = selectedAction.meaning;
        summaryView.textContent = selectedAction.view;
        summaryExample.textContent = selectedAction.example;

        if (selectedAction.type === "push") {
            phonePreview.classList.add("active");
            defaultExample.classList.add("hidden");

            pushTitle.textContent = selectedAction.pushTitle;
            pushText.textContent = selectedAction.pushText;
        } else {
            phonePreview.classList.remove("active");
            defaultExample.classList.remove("hidden");
        }

        if (selectedAction.type === "typing") {
            defaultExample.classList.add("typing-demo");
            startTypingAnimation();
        } else {
            defaultExample.classList.remove("typing-demo");
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
        tg.showAlert("Сначала выберите действие");
        return;
    }

    const data = {
        service: selectedAction.title,
        theme: "Действия собеседника",
        user: tg.initDataUnsafe.user || null
    };

    tg.sendData(JSON.stringify(data));
    tg.close();
});