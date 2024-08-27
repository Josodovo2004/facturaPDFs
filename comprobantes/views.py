from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.units import cm # type: ignore
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pdfFacturacion.settings import env
import json
import os
import requests

@csrf_exempt
def create_pdf_comprobante(request):
    try:
        data = json.loads(request.body, )

        # Convert the data to JSON format
        json_data = json.dumps(data)

        # Send the POST request to emitirComprobante endpoint
        response = requests.post(env('URLFACTURACION'), data=json_data, headers={"Content-Type": "application/json"})

        json_data = response.json()

        # Extract the hash_code
        hash_code = json_data.get('hash_code')

        if hash_code is None:
            return JsonResponse({'error' : 'no se proceso el hashCode'})
        # Definir el directorio de destino para los archivos PDF
        pdf_dir = os.path.join(settings.MEDIA_URL, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        file_name = f'{data['comprobante']['serieDocumento']}-{data['comprobante']['numeroDocumento']}.pdf'

        # Ruta completa del archivo PDF
        file_path = os.path.join(pdf_dir, file_name)
        
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        
        # Margen
        margin = 2 * cm
        
        # Títulos y encabezados
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, height - margin, "Comprobante de Venta")
        
        c.setFont("Helvetica", 12)
        c.drawString(margin, height - 2 * margin, f"Serie y Número: {data['comprobante']['serieDocumento']}-{data['comprobante']['numeroDocumento']}")
        c.drawString(margin, height - 3 * margin, f"Fecha de Emisión: {data['comprobante']['fechaEmision']}")
        c.drawString(margin, height - 4 * margin, f"Vencimiento: {data['comprobante']['DueDate']}")
        
        c.drawString(margin, height - 5 * margin, f"Emisor: {data['emisor']['RazonSocialEmisor']}")
        c.drawString(margin, height - 6 * margin, f"RUC: {data['emisor']['DocumentoEmisor']}")
        
        c.drawString(margin, height - 7 * margin, f"Cliente: {data['adquiriente']['razonSocial']}")
        c.drawString(margin, height - 8 * margin, f"DNI/RUC: {data['adquiriente']['NumeroDocumentoAdquiriente']}")
        
        c.drawString(margin, height - 9 * margin, f"Dirección: {data['adquiriente']['CalleComprador']}, {data['adquiriente']['distritoComprador']}, {data['adquiriente']['provinciaComprador']}, {data['adquiriente']['departamentoComprador']}")
        
        # Línea horizontal para separar secciones
        c.line(margin, height - 10 * cm, width - margin, height - 10 * cm)
        
        # Tabla de Items
        y_position = height - 11 * cm
        item_height = 0.5 * cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y_position, "Descripción")
        c.drawString(margin + 7 * cm, y_position, "Cantidad")
        c.drawString(margin + 10 * cm, y_position, "Precio Unitario")
        c.drawString(margin + 13 * cm, y_position, "Total")
        
        c.setFont("Helvetica", 10)
        
        y_position -= item_height
        for item in data["Items"]:
            c.drawString(margin, y_position, item["DescripcionItem"])
            c.drawString(margin + 7 * cm, y_position, str(item["CantidadUnidadesItem"]))
            c.drawString(margin + 10 * cm, y_position, f"S/{item['precioUnitario']:.2f}")
            c.drawString(margin + 13 * cm, y_position, f"S/{item['totalValorVenta']:.2f}")
            y_position -= item_height
        
        # Totales
        y_position -= 1 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin + 10 * cm, y_position, "Subtotal:")
        c.drawString(margin + 13 * cm, y_position, f"S/{data['comprobante']['ImporteTotalVenta']:.2f}")
        
        y_position -= item_height
        c.drawString(margin + 10 * cm, y_position, "IGV:")
        c.drawString(margin + 13 * cm, y_position, f"S/{data['comprobante']['MontoTotalImpuestos']:.2f}")
        
        y_position -= item_height
        c.drawString(margin + 10 * cm, y_position, "Total:")
        c.drawString(margin + 13 * cm, y_position, f"S/{data['comprobante']['totalConImpuestos']:.2f}")
        
        c.save()
        file_url = f'{file_path}'
        return JsonResponse({'pdf_url': file_url})
    except Exception as e:
        print(e)
