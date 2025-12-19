import os
from typing import List, Optional

BASE_IMAGE_PATH = "imagens"  # pasta atual onde as imagens irao, caso testar local ze <<<_------

def get_image_path(filename: str) -> str:
    """
    retorna o caminho local da imagem.
    depois basta trocar para URL R2.
    """
    return os.path.join(BASE_IMAGE_PATH, filename)

def get_images_paths(images: Optional[List[str]]) -> List[str]:
    if not images:
        return []
    return [get_image_path(img) for img in images]


##### quando tiver bucket no r2, substituir 
#from typing import List, Optional

#BASE_IMAGE_PATH = "imagens"

#def get_image_path(filename: str) -> str:
    #return f"{BASE_IMAGE_PATH}/{filename}"

#def get_images_paths(files: Optional[List[str]]) -> List[str]:
    if not files:
        return []
    base = BASE_IMAGE_PATH
    return [f"{base}/{f}" for f in files]