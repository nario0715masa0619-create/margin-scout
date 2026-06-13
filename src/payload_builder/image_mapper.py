"""
Image Mapper

ローカル画像ディレクトリを eBay payload 用の image list に変換
"""

from typing import List, Dict

class ImageMapper:
    """
    image_dir → image_list への変換
    
    data/images/{SKU}/ をスキャンして、
    01.jpg, 02.jpg, ... を順序付きで返す
    """
    
    def __init__(self, base_image_dir: str = "data/images"):
        self.base_image_dir = base_image_dir
        
    def map_images(
        self,
        sku: str,
        image_count: int
    ) -> tuple[List[str], Dict]:
        """
        SKU からローカル画像 list を生成
        
        Returns:
            (image_list, metadata)
        """
        # TODO: ディレクトリスキャンロジック実装
        # TODO: ゼロパディング順序確認
        # TODO: 画像ファイル存在確認
        # TODO: 拡張子チェック (.jpg)
        raise NotImplementedError("Image mapper implementation pending Phase 4")
        
    def validate_images(
        self,
        image_dir: str,
        image_count: int
    ) -> tuple[bool, List[str]]:
        """
        画像ディレクトリ・ファイル検証
        
        Returns:
            (valid, warnings)
        """
        # TODO: ディレクトリ存在確認
        # TODO: ファイル数確認
        # TODO: ファイル形式確認
        raise NotImplementedError("Image validation implementation pending Phase 4")
