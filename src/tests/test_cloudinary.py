import pytest
from unittest.mock import MagicMock, patch
from fastapi import UploadFile
from src.services.cloudinary_service import UploadFileService

# Створюємо фікстуру для нашого сервісу
@pytest.fixture
def upload_file_service():
    # Заглушуємо __init__, щоб не викликати реальне налаштування Cloudinary
    with patch('src.services.cloudinary_service.cloudinary.config'):
        service = UploadFileService("mock_cloud", "mock_key", "mock_secret")
        yield service

@pytest.mark.asyncio
@patch('src.services.cloudinary_service.cloudinary.uploader.upload')
@patch('src.services.cloudinary_service.cloudinary.CloudinaryImage')
async def test_upload_file(mock_cloudinary_image, mock_uploader_upload, upload_file_service):
    """
    Test the upload_file method.
    """
    # Встановлюємо, що мають повертати заглушки
    mock_uploader_upload.return_value = {"version": "1234567890"}
    
    mock_image_instance = MagicMock()
    mock_image_instance.build_url.return_value = "http://mocked.url/RestApp/test_user"
    mock_cloudinary_image.return_value = mock_image_instance

    # Створюємо заглушку для файлу, який будемо завантажувати
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = MagicMock()

    # Викликаємо метод
    result_url = upload_file_service.upload_file(mock_file, "test_user")

    # Перевіряємо, що upload було викликано з правильними аргументами
    mock_uploader_upload.assert_called_once_with(
        mock_file.file, 
        public_id="RestApp/test_user", 
        overwrite=True
    )
    
    # Перевіряємо, що CloudinaryImage було викликано з правильним public_id
    mock_cloudinary_image.assert_called_once_with("RestApp/test_user")

    # Перевіряємо, що build_url було викликано
    mock_image_instance.build_url.assert_called_once_with(
        width=250, 
        height=250, 
        crop="fill", 
        version="1234567890"
    )

    # Перевіряємо, що метод повернув очікуваний URL
    assert result_url == "http://mocked.url/RestApp/test_user"


