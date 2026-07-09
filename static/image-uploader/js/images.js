document.addEventListener('DOMContentLoaded', () => {
    // Блокировка F5 и Escape
    document.addEventListener('keydown', function (event) {
        if (event.key === 'F5' || event.key === 'Escape') {
            event.preventDefault();
            window.location.href = 'upload.html';
        }
    });

    const fileListWrapper = document.getElementById('file-list-wrapper');
    const uploadRedirectButton = document.getElementById('upload-tab-btn');
    let currentPage = 1;

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

    const fetchAndDisplayImages = async (page = 1) => {
        try {
            const response = await fetch(`/api/images?page=${page}`);
            if (!response.ok) {
                throw new Error('Не удалось загрузить список изображений');
            }
            const data = await response.json();
            displayImages(data.items, data.total, data.page, data.page_size);
        } catch (error) {
            console.error('Ошибка при загрузке списка:', error);
            fileListWrapper.innerHTML = '<p style="color: red;">Не удалось загрузить список изображений.</p>';
        }
    };

    const displayImages = (images, total, page, pageSize) => {
        fileListWrapper.innerHTML = '';

        if (!images || images.length === 0) {
            fileListWrapper.innerHTML = '<p>No images uploaded yet.</p>';
            return;
        }

        const container = document.createElement('div');
        container.className = 'file-list-container';

        // Заголовок таблицы с новыми колонками
        const header = document.createElement('div');
        header.className = 'file-list-header';
        header.innerHTML = `
            <span class="file-col file-col-name">Name</span>
            <span class="file-col file-col-size">Size</span>
            <span class="file-col file-col-date">Upload Time</span>
            <span class="file-col file-col-url">Url</span>
            <span class="file-col file-col-delete">Delete</span>
        `;
        container.appendChild(header);

        const list = document.createElement('div');
        list.id = 'file-list';

        images.forEach((imgData) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-list-item';

            // Форматирование размера
            let sizeStr = '';
            if (imgData.size < 1024) {
                sizeStr = imgData.size + ' B';
            } else if (imgData.size < 1024 * 1024) {
                sizeStr = (imgData.size / 1024).toFixed(1) + ' KB';
            } else {
                sizeStr = (imgData.size / (1024 * 1024)).toFixed(1) + ' MB';
            }

            const fullUrl = window.location.origin + '/images/' + imgData.filename;
            fileItem.innerHTML = `
                <span class="file-col file-col-name">
                    <span class="file-icon">🖼️</span>
                    <span class="file-name">${imgData.original_name}</span>
                </span>
                <span class="file-col file-col-size">${sizeStr}</span>
                <span class="file-col file-col-date">${imgData.upload_time}</span>
                <span class="file-col file-col-url">
                    <a href="${fullUrl}" target="_blank">${fullUrl}</a>
                </span>
                <span class="file-col file-col-delete">
                    <button class="delete-btn" data-filename="${imgData.filename}">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2">
                            <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                            <line x1="10" y1="11" x2="10" y2="17"/>
                            <line x1="14" y1="11" x2="14" y2="17"/>
                        </svg>
                    </button>
                </span>
            `;
            list.appendChild(fileItem);
        });

        container.appendChild(list);

        // Пагинация
        const totalPages = Math.ceil(total / pageSize);
        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination';
        if (page > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.textContent = 'Previous';
            prevBtn.addEventListener('click', () => {
                currentPage = page - 1;
                fetchAndDisplayImages(currentPage);
            });
            paginationDiv.appendChild(prevBtn);
        }
        for (let i = 1; i <= totalPages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            if (i === page) {
                pageBtn.disabled = true;
                pageBtn.style.fontWeight = 'bold';
            }
            pageBtn.addEventListener('click', () => {
                currentPage = i;
                fetchAndDisplayImages(currentPage);
            });
            paginationDiv.appendChild(pageBtn);
        }
        if (page < totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'Next';
            nextBtn.addEventListener('click', () => {
                currentPage = page + 1;
                fetchAndDisplayImages(currentPage);
            });
            paginationDiv.appendChild(nextBtn);
        }
        container.appendChild(paginationDiv);

        fileListWrapper.appendChild(container);

        // Обработчики удаления
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const filename = event.currentTarget.dataset.filename;
                if (confirm(`Удалить изображение "${filename}"?`)) {
                    await deleteImage(filename);
                }
            });
        });

        updateTabStyles();
    };

    const deleteImage = async (filename) => {
        try {
            const response = await fetch(`/api/delete/${filename}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(`Ошибка при удалении: ${errorData.error || 'Неизвестная ошибка'}`);
                return;
            }

            await fetchAndDisplayImages(currentPage);
            alert(`Изображение "${filename}" удалено.`);
        } catch (error) {
            console.error('Ошибка при удалении:', error);
            alert('Произошла ошибка при удалении файла.');
        }
    };

    if (uploadRedirectButton) {
        uploadRedirectButton.addEventListener('click', () => {
            window.location.href = 'upload.html';
        });
    }

    fetchAndDisplayImages(currentPage);
});