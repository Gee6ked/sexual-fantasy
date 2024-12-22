// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;

// Готовность WebApp
tg.ready();

// Получение данных пользователя
const user = tg.initDataUnsafe.user;

// Флаги и данные пользователя
let isRegistered = false;
let userData = {};
let selectedLocation = null;
let map, marker;

let lastSelectedTab = null;  
let infoVisibleMap = {
    music: false,
    videos: false,
    merch: false,
    game: false,
    info: false
};

const artistInfo = {
    "Kai Cenat": {
        "image": "https://s.yimg.com/ny/api/res/1.2/G_qIOmAD7ucEf5A6XaoDbQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTcyMA--/https://media.zenfs.com/en/insider_articles_922/46501b74228509bf79e0e65f9381e965",
        "description": "Kai Cenat is a widely recognized YouTube and Twitch streamer known for his entertaining content, comedic skits, and engaging live streams. He has built a loyal fanbase with his charismatic personality and creative approach to content creation. Kai often collaborates with other prominent creators and has become a cultural icon within the online streaming community."
    },
    "Lil Uzi Vert": {
        "image": "https://i.ytimg.com/vi/ejhkUexvn9M/maxresdefault.jpg?sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AHUBoAC4AOKAgwIABABGGAgZShHMA8=&rs=AOn4CLCHgFp_MTitTJgIFbNNRvYKGZJASQ",
        "description": "Lil Uzi Vert is a highly influential American rapper and singer, known for his unique style, vibrant personality, and chart-topping hits like 'XO TOUR Llif3.' With his eccentric fashion sense and genre-blending music, Lil Uzi Vert has redefined modern hip-hop, garnering a massive global following and critical acclaim for his creativity and innovation in the industry."
    },
    "Kanye West": {
        "image": "https://avatars.mds.yandex.net/i?id=d2644e69ac93802a5ae1b5e89d42e1f0_l-5151057-images-thumbs&n=13",
        "description": "Kanye West, also known as Ye, is an iconic American rapper, producer, and entrepreneur. As one of the most influential figures in music history, Kanye has revolutionized hip-hop with groundbreaking albums like 'The College Dropout' and 'My Beautiful Dark Twisted Fantasy.' Beyond music, Kanye is a fashion mogul and cultural visionary, shaping trends and sparking conversations worldwide."
    },
    "Bradley Cooper": {
        "image": "https://media.zenfs.com/en/cnn_articles_875/6f74951abb69df56a2d98db34bc2b791",
        "description": "Bradley Cooper is an acclaimed American actor and filmmaker, celebrated for his roles in films like 'Silver Linings Playbook,' 'A Star is Born,' and 'American Sniper.' Known for his versatile acting skills and dedication to his craft, Cooper has earned numerous awards and nominations, solidifying his place as one of Hollywood's most respected talents."
    },
    "Yung Lean": {
        "image": "https://i.ytimg.com/vi/AbSSch--j1I/maxresdefault.jpg",
        "description": "Yung Lean is a groundbreaking Swedish rapper, singer, and producer, widely regarded as a pioneer in the 'cloud rap' genre. Emerging from the underground scene, Yung Lean gained international fame with hits like 'Ginseng Strip 2002' and his unique, melancholic style. He remains a key figure in modern alternative hip-hop, influencing countless artists worldwide."
    },
    "Rich Amiri": {
        "image": "https://4shomag.com/wp-content/uploads/2023/03/Untitled-1000x600.jpg",
        "description": "Rich Amiri is a rising star in the music industry, known for his catchy melodies and genre-bending tracks. With a fresh approach to songwriting and production, Rich Amiri has quickly gained attention as one of the most promising new talents. His dedication to his craft and innovative sound make him a name to watch in the coming years."
    },
    "Ken Carson": {
        "image": "https://i.ytimg.com/vi/c51LMU8Bvj0/maxresdefault.jpg",
        "description": "Ken Carson is a dynamic artist making waves in the music scene. Known for his high-energy performances and unique sound, he is quickly carving out his space in the industry. Fans are drawn to his bold approach to music, blending genres and pushing boundaries, making him a standout among emerging musicians."
    },
    "PLOHOYPAREN": {
        "image": "https://i.ytimg.com/vi/9Ea9DNA9Rd4/maxresdefault.jpg",
        "description": "PLOHOYPAREN is a rising music artist recognized for their emotive and introspective tracks. With a growing fanbase, their music resonates deeply with listeners, blending personal storytelling with captivating beats. PLOHOYPAREN is on a path to establish themselves as a significant voice in modern music."
    },
    "Platina": {
        "image": "https://aif-s3.aif.ru/images/036/711/971d53a6e43ff450af7911857039c68a.png",
        "description": "Platina is a talented artist gaining recognition in the music world for their distinctive sound and compelling lyrics. Their ability to connect with audiences through relatable themes and innovative production makes them a standout talent in today's competitive music landscape."
    }
};

// Открытие/закрытие модалок
function openModal() {
    if (!isRegistered) {
        restoreRegistrationForm(); // Заполнение содержимого формы регистрации
    } else {
        showUserData(); // Показываем данные пользователя
    }
    document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

function openPrivacyModal() {
    document.getElementById('privacyModal').style.display = 'flex';
}

function closePrivacyModal() {
    document.getElementById('privacyModal').style.display = 'none';
}

function openTermsModal() {
    document.getElementById('termsModal').style.display = 'flex';
}

function closeTermsModal() {
    document.getElementById('termsModal').style.display = 'none';
}

function openVideoModal(videoUrl) {
    const modal = document.getElementById('videoModal');
    const iframe = modal.querySelector('iframe');
    iframe.src = videoUrl;
    modal.style.display = 'flex';
}

function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    modal.style.display = 'none';
    const iframe = modal.querySelector('iframe');
    iframe.src = '';
}

function openArtistInfoModal(artistName) {
    const modal = document.getElementById('artistInfoModal');
    const nameElement = document.getElementById('artistName');
    const imageElement = document.getElementById('artistImage');
    const descriptionElement = document.getElementById('artistDescription');

    const info = artistInfo[artistName];
    if (info) {
        nameElement.textContent = artistName;
        imageElement.src = info.image;
        imageElement.alt = artistName;
        descriptionElement.textContent = info.description;
        modal.style.display = 'flex';
    } else {
        alert('Информация об этом артисте недоступна.');
    }
}

function closeArtistInfoModal() {
    document.getElementById('artistInfoModal').style.display = 'none';
}

// Регистрация
function handleRegistration(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const email = document.getElementById('emailInput').value;
    const password = document.getElementById('password').value;

    userData = { username, email };
    isRegistered = true;

    // Сохраняем данные в localStorage
    localStorage.setItem('isRegistered', 'true');
    localStorage.setItem('userData', JSON.stringify(userData));

    alert('Регистрация успешна!');
    showMapAfterRegistration();

    // Отправка данных в бот
    sendDataToBot({
        type: 'registration',
        data: userData
    });
}

function sendDataToBot(payload) {
    tg.sendData(JSON.stringify(payload));
}

function showMapAfterRegistration() {
    const form = document.getElementById('registrationForm');
    form.style.display = 'none';

    const modalTitle = document.getElementById('modalTitle');
    modalTitle.textContent = "Выбор локации";

    const modalDescription = document.getElementById('modalDescription');
    modalDescription.textContent = "Выберите локацию на карте Франции:";

    document.getElementById('map').style.display = 'block';
    document.querySelector('.confirm-location-button').style.display = 'block';

    initMap();
}

function initMap() {
    map = L.map('map').setView([46.2276, 2.2137], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function(e) {
        placeMarker(e.latlng);
    });

    if (userData.location) {
        const latlng = userData.location;
        marker = L.marker([latlng.lat, latlng.lng]).addTo(map);
        map.setView([latlng.lat, latlng.lng], 10);
    }
}

function placeMarker(latlng) {
    if (marker) {
        map.removeLayer(marker);
    }
    marker = L.marker(latlng).addTo(map);
    selectedLocation = { lat: latlng.lat, lng: latlng.lng };
}

async function confirmLocation() {
    if (selectedLocation) {
        userData.location = selectedLocation;
        const url = `https://nominatim.openstreetmap.org/reverse?lat=${selectedLocation.lat}&lon=${selectedLocation.lng}&format=jsonv2`;
        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data && data.display_name) {
                userData.locationAddress = data.display_name;
            } else {
                userData.locationAddress = 'Адрес не найден';
            }
        } catch (error) {
            userData.locationAddress = 'Ошибка определения адреса';
        }

        localStorage.setItem('userData', JSON.stringify(userData));

        alert(`Локация выбрана: ${selectedLocation.lat}, ${selectedLocation.lng}\nАдрес: ${userData.locationAddress}`);
        closeModal();

        // Отправка данных в бот
        sendDataToBot({
            type: 'location',
            data: {
                coordinates: selectedLocation,
                address: userData.locationAddress
            }
        });
    } else {
        alert('Сначала выберите локацию на карте.');
    }
}

function handleLogoClick() {
    if (isRegistered) {
        showUserData();
    } else {
        openModal(); // Теперь openModal сам вызывает restoreRegistrationForm
    }
}

function showUserData() {
    let locationInfo = '';
    if (userData.location) {
        locationInfo = `<br><strong>Локация (координаты):</strong> ${userData.location.lat}, ${userData.location.lng}`;
        if (userData.locationAddress) {
            locationInfo += `<br><strong>Адрес:</strong> ${userData.locationAddress}`;
        }
    }

    document.getElementById('modalContent').innerHTML = `
        <span class="close" onclick="closeModal()">&times;</span>
        <div class="modal-title">Добро пожаловать!</div>
        <div class="modal-description">
            Вы успешно зарегистрированы.<br><br>
            <strong>Имя пользователя:</strong> ${userData.username}<br>
            <strong>Email:</strong> ${userData.email}
            ${locationInfo}
        </div>
        <button class="grey-button" onclick="logout()">Выйти из аккаунта</button>
    `;
    openModal();
}

function logout() {
    isRegistered = false;
    userData = {};
    selectedLocation = null;

    localStorage.removeItem('isRegistered');
    localStorage.removeItem('userData');

    alert('Вы вышли из аккаунта.');
    closeModal();
    restoreRegistrationForm();

    // Отправка данных в бот
    sendDataToBot({
        type: 'logout'
    });
}

function restoreRegistrationForm() {
    document.getElementById('modalContent').innerHTML = `
        <span class="close" onclick="closeModal()">&times;</span>
        <div class="modal-title" id="modalTitle">Регистрация</div>
        <div class="modal-description" id="modalDescription">Создайте аккаунт, чтобы получить доступ к эксклюзивному контенту.</div>
        <form id="registrationForm" onsubmit="handleRegistration(event)">
            <label for="username">Имя пользователя</label>
            <input type="text" id="username" placeholder="Введите имя пользователя" required>
            <label for="emailInput">Электронная почта</label>
            <input type="email" id="emailInput" placeholder="Введите email" required>
            <label for="password">Пароль</label>
            <input type="password" id="password" placeholder="Введите пароль" required>
            <button type="submit">Зарегистрироваться</button>
        </form>
        <div id="map" style="display:none;"></div>
        <button class="confirm-location-button" style="display:none;" onclick="confirmLocation()">Подтвердить локацию</button>
    `;
}

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
        const p = tab.querySelector('p');
        if (p) p.style.display = 'none';
    });
    document.getElementById(tabId).classList.add('active');

    // Показываем игру, если выбрана вкладка "game"
    if (tabId === 'game') {
        document.getElementById('mario-game-container').style.display = 'block';
        initializeGame();
    } else {
        // Скрываем игру при переключении на другие вкладки
        if (document.getElementById('mario-game-container')) {
            document.getElementById('mario-game-container').style.display = 'none';
        }
    }

    if (tabId !== lastSelectedTab) {
        infoVisibleMap[tabId] = false; 
        lastSelectedTab = tabId;
    } else {
        toggleInfo(tabId);
    }
}

function toggleInfo(tabId) {
    const tab = document.getElementById(tabId);
    const paragraph = tab.querySelector('p');
    if (paragraph) {
        if (infoVisibleMap[tabId]) {
            paragraph.style.display = 'none';
            infoVisibleMap[tabId] = false;
        } else {
            paragraph.style.display = 'block';
            infoVisibleMap[tabId] = true;
        }
    }
}

// Инициализация игры
let gameInitialized = false;
function initializeGame() {
    if (gameInitialized) return;
    gameInitialized = true;

    const canvas = document.getElementById('gameCanvas');
    if (!canvas) return; // Если нет canvas, выходим

    const ctx = canvas.getContext('2d');

    const gravity = 0.7;
    const friction = 0.9;
    const keys = {};

    const player = {
        x: 100,
        y: 500,
        width: 50,
        height: 50,
        color: 'red',
        dx: 0,
        dy: 0,
        speed: 10,
        jumping: false
    };

    const platforms = [
        {x: 0, y: 550, width: 800, height: 50},
        {x: 150, y: 450, width: 100, height: 20},
        {x: 300, y: 350, width: 100, height: 20},
        {x: 450, y: 250, width: 100, height: 20},
        {x: 600, y: 350, width: 100, height: 20},
        {x: 750, y: 450, width: 100, height: 20},
    ];

    window.addEventListener('keydown', function(e) {
        keys[e.code] = true;
    });

    window.addEventListener('keyup', function(e) {
        keys[e.code] = false;
    });

    function update() {
        if (keys['ArrowRight'] || keys['KeyD']) {
            player.dx = player.speed;
        } else if (keys['ArrowLeft'] || keys['KeyA']) {
            player.dx = -player.speed;
        } else {
            player.dx *= friction;
        }

        if ((keys['ArrowUp'] || keys['KeyW'] || keys['Space']) && !player.jumping) {
            player.dy = -12;
            player.jumping = true;
        }

        player.dy += gravity;

        player.x += player.dx;
        player.y += player.dy;

        if (player.x < 0) player.x = 0;
        if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;
        if (player.y + player.height > canvas.height) {
            player.y = canvas.height - player.height;
            player.dy = 0;
            player.jumping = false;
        }

        platforms.forEach(platform => {
            if (
                player.x < platform.x + platform.width &&
                player.x + player.width > platform.x &&
                player.y + player.height < platform.y + platform.height &&
                player.y + player.height + player.dy >= platform.y
            ) {
                player.y = platform.y - player.height;
                player.dy = 0;
                player.jumping = false;
            }
        });

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = player.color;
        ctx.fillRect(player.x, player.y, player.width, player.height);

        ctx.fillStyle = 'green';
        platforms.forEach(platform => {
            ctx.fillRect(platform.x, platform.y, platform.width, platform.height);
        });

        requestAnimationFrame(update);
    }

    update();
}

document.addEventListener('DOMContentLoaded', () => {
    const storedIsRegistered = localStorage.getItem('isRegistered');
    const storedUserData = localStorage.getItem('userData');

    if (storedIsRegistered === 'true' && storedUserData) {
        isRegistered = true;
        userData = JSON.parse(storedUserData);
    }
    const albums = document.querySelectorAll('.album');
    albums.forEach(album => {
        album.addEventListener('click', () => {
            const artistName = album.getAttribute('data-artist');
            openArtistInfoModal(artistName);
        });
    });

    // Если пользователь уже зарегистрирован, показываем его данные при загрузке страницы
    if (isRegistered) {
        showUserData();
    }
});

// Обработка событий от Telegram бота
tg.onEvent('mainButtonClicked', () => {
    openModal();
});

tg.onEvent('data', (event) => {
    const payload = JSON.parse(event.data);
    // Обработка данных, полученных от WebApp
    console.log('Received data from WebApp:', payload);
    // Добавьте здесь логику обработки данных
    // Например, вы можете отправить эти данные на ваш сервер для дальнейшей обработки
});