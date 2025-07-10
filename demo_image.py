#!/usr/bin/env python3
"""
Cria uma imagem de teste para demonstração
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_demo_image():
    """Cria uma imagem de demonstração simulando um pedido de venda"""
    # Criar uma imagem branca
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Tentar usar fonte padrão
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()
    
    # Desenhar cabeçalho
    draw.text((50, 30), "PEDIDO DE VENDA #2024-001", fill='black', font=font_large)
    draw.text((50, 70), "Cliente: Empresa ABC Ltda", fill='black', font=font_normal)
    draw.text((50, 95), "Data: 10/07/2024", fill='black', font=font_normal)
    
    # Linha separadora
    draw.line([(50, 130), (750, 130)], fill='black', width=2)
    
    # Cabeçalho da tabela
    draw.text((50, 150), "PRODUTOS:", fill='black', font=font_large)
    
    # Produtos de exemplo
    produtos = [
        "Cod: P001 | Parafuso M6x20mm | Qtd: 100 | Valor Unit: R$ 0,50 | Total: R$ 50,00",
        "Cod: P002 | Arruela Lisa M6 | Qtd: 200 | Valor Unit: R$ 0,10 | Total: R$ 20,00",
        "Cod: P003 | Porca Sextavada M6 | Qtd: 100 | Valor Unit: R$ 0,30 | Total: R$ 30,00",
        "Cod: P004 | Parafuso M8x25mm | Qtd: 50 | Valor Unit: R$ 0,80 | Total: R$ 40,00"
    ]
    
    y_pos = 190
    for produto in produtos:
        draw.text((50, y_pos), produto, fill='black', font=font_normal)
        y_pos += 25
    
    # Linha separadora
    draw.line([(50, y_pos + 10), (750, y_pos + 10)], fill='black', width=2)
    
    # Total
    draw.text((50, y_pos + 30), "TOTAL GERAL: R$ 140,00", fill='black', font=font_large)
    
    # Rodapé
    draw.text((50, height - 50), "Documento gerado para teste do sistema", fill='gray', font=font_normal)
    
    # Salvar imagem
    output_path = os.path.join('uploads', 'demo_pedido.png')
    os.makedirs('uploads', exist_ok=True)
    img.save(output_path)
    
    print(f"✓ Imagem de demonstração criada: {output_path}")
    return output_path

if __name__ == "__main__":
    create_demo_image()