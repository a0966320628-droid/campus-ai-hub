import os
import uuid
from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def get_extension(filename):
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()

def is_allowed_file(filename, allowed_extensions):
    return get_extension(filename) in set(allowed_extensions)

def save_uploaded_file(file_storage, folder, allowed_extensions, prefix="file"):
    if not file_storage or not file_storage.filename:
        return None

    original_name = secure_filename(file_storage.filename)
    extension = get_extension(original_name)

    if extension not in set(allowed_extensions):
        raise ValueError("不支援的檔案格式")

    os.makedirs(folder, exist_ok=True)
    stored_name = f"{prefix}_{uuid.uuid4().hex}.{extension}"
    save_path = os.path.join(folder, stored_name)
    file_storage.save(save_path)

    return {
        "original_name": original_name,
        "stored_name": stored_name,
        "save_path": save_path,
        "extension": extension,
    }

def delete_file_if_exists(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
