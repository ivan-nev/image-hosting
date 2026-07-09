document.addEventListener('DOMContentLoaded', function () {
    // Блокировка F5 и Escape (оставляем как есть)
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' || event.key === 'F5') {
            event.preventDefault();
            sessionStorage.removeItem('pageWasVisited');
            window.location.href = '../index.html';
        }
    });

    const fileUpload = document.getElementById('file-upload');
    const imagesButton = document.getElementById('images-tab-btn');
    const dropzone = document.querySelector('.upload__dropzone');
    const currentUploadInput = document.querySelector('.upload__input');
    const copyButton = document.querySelector('.upload__copy');

    // Функция для обновления активной вкладки
    const updateTabStyles = () => {
        const uploadTab = document.getElementById('upload-tab-btn');
        const imagesTab = document.getElementById('images-tab-btn');
        const isImagesPage = window.location.pathname.includes('images.html');
        uploadTab.classList.remove('upload__tab--active');
        imagesTab.classList.remove('upload__tab--active');
        if (isImagesPage) {
            imagesTab.classList.add('upload__tab--active');
        } else {
            uploadTab.classList.add('upload__tab--active');
        }
    };

    // Функция для отправки файла на сервер
    const uploadFileToServer = async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                alert(`Ошибка: ${result.error || 'Неизвестная ошибка'}`);
                return;
            }

            // Успешная загрузка
            if (result.success) {
                if (currentUploadInput) {
                    // Используем URL, полученный от сервера
                    const fullUrl = window.location.origin + result.url;
                    currentUploadInput.value = fullUrl;
                }
                alert(`Файл "${result.original_name}" успешно загружен!`);
            } else {
                alert(`Ошибка: ${result.error || 'Неизвестная ошибка'}`);
            }
        } catch (error) {
            console.error('Ошибка при загрузке:', error);
            alert('Произошла ошибка при загрузке файла.');
        }
    };

    // Обработчик выбора файла
    if (fileUpload) {
        fileUpload.addEventListener('change', (event) => {
            const files = event.target.files;
            if (files.length > 0) {
                uploadFileToServer(files[0]);
            }
            event.target.value = ''; // Сброс поля
        });
    }

    // Обработчик кнопки "Images"
    if (imagesButton) {
        imagesButton.addEventListener('click', () => {
            window.location.href = 'images.html';
        });
    }

    // Обработчик кнопки копирования
    if (copyButton && currentUploadInput) {
        copyButton.addEventListener('click', () => {
            const textToCopy = currentUploadInput.value;
            if (textToCopy && textToCopy !== 'https://') {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    copyButton.textContent = 'COPIED!';
                    setTimeout(() => {
                        copyButton.textContent = 'COPY';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            }
        });
    }

    // Drag and Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        if (dropzone) {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        }
    });

    if (dropzone) {
        dropzone.addEventListener('drop', (event) => {
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                uploadFileToServer(files[0]);
            }
        });
    }

    updateTabStyles();
});