
# app/services/qr_service.py
import qrcode
from io import BytesIO
import base64
from typing import Optional
from pyzbar.pyzbar import decode
from PIL import Image

class QRService:
    @staticmethod
    def generate_qr_code(data: str) -> BytesIO:
        """
        Gera um QR Code a partir de uma string e retorna o objeto BytesIO (imagem)
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

    @staticmethod
    def generate_qr_base64(data: str) -> str:
        """
        Retorna a string base64 do QR Code para embutir em HTML/JSON
        """
        img_io = QRService.generate_qr_code(data)
        return base64.b64encode(img_io.getvalue()).decode('utf-8')

    @staticmethod
    def decode_qr_image(file_bytes: bytes) -> Optional[str]:
        """
        Lê um QR code de bytes de imagem
        """
        try:
            img = Image.open(BytesIO(file_bytes))
            decoded_objects = decode(img)
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8')
            return None
        except Exception:
            return None
