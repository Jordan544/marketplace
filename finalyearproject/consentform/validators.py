# consentform/validators.py
import os
from django.core.exceptions import ValidationError

def validate_image_extension_and_size(image):
    # 1. Check file extension
    ext = os.path.splitext(image.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file extension. Please upload a .jpg, .jpeg, .png, or .webp image.')
    
    # 2. Check file size (Limit to 3MB)
    max_size_mb = 3
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'File size too large. Maximum allowed size is {max_size_mb}MB.')