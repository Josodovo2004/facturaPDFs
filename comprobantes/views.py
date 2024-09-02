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
import qrcode # type: ignore
from io import BytesIO
from reportlab.lib.utils import ImageReader # type: ignore

@csrf_exempt
def create_pdf_comprobante(request):
    try:
        data = json.loads(request.body)

        # Convert the data to JSON format
        json_data = json.dumps(data)

        # Send the POST request to emitirComprobante endpoint
        response = requests.post(env('URLFACTURACION'), data=json_data, headers={"Content-Type": "application/json"})

        # Check if the request was successful
        if response.status_code != 200:
            return JsonResponse({'error': f"Error en la solicitud: {response.status_code}"})

        try:
            json_data = response.json()
        except ValueError:
            return JsonResponse({'error': 'La respuesta no es un JSON válido'})

        # Extract the hash_code
        hash_code = json_data.get('hash_code')
        if hash_code is None:
            return JsonResponse({'error': 'No se procesó el hashCode'})

        # Define the directory for PDF files
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)

        file_name = f"{data['comprobante']['serieDocumento']}-{data['comprobante']['numeroDocumento']}.pdf"

        # Full file path for the PDF
        file_path = os.path.join(pdf_dir, file_name)

        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        # Margin
        margin = 2 * cm

        currenty = height - 2 * margin

        # Titles and headers
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, height - margin, "Comprobante de Venta")

        c.setFont("Helvetica", 12)
        c.drawString(margin, currenty, f"Serie y Número: {data['comprobante']['serieDocumento']}-{data['comprobante']['numeroDocumento']}")
        c.drawString(margin, currenty - 20, f"Fecha de Emisión: {data['comprobante']['fechaEmision']}")
        c.drawString(margin, currenty - 40, f"Vencimiento: {data['comprobante']['DueDate']}")

        c.drawString(margin, currenty - 320, f"Emisor: {data['emisor']['RazonSocialEmisor']}")
        c.drawString(margin, currenty - 340, f"RUC: {data['emisor']['DocumentoEmisor']}")

        c.drawString(margin, currenty - 360, f"Cliente: {data['adquiriente']['razonSocial']}")
        c.drawString(margin, currenty - 380, f"DNI/RUC: {data['adquiriente']['NumeroDocumentoAdquiriente']}")
        
        c.drawString(margin, currenty - 400, f"Dirección: {data['adquiriente']['CalleComprador']}, {data['adquiriente']['distritoComprador']}, {data['adquiriente']['provinciaComprador']}, {data['adquiriente']['departamentoComprador']}")

        # Horizontal line to separate sections
        c.line(margin, height - 10.1 * cm, width - margin, height - 10.1 * cm)

        # Table Headers
        y_position = height - 11 * cm
        item_height = 0.5 * cm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y_position, "Descripción")
        c.drawString(margin + 7 * cm, y_position, "Cantidad")
        c.drawString(margin + 10 * cm, y_position, "Precio Unitario")
        c.drawString(margin + 13 * cm, y_position, "Total")

        # Table Rows
        c.setFont("Helvetica", 10)
        y_position -= item_height
        for item in data["Items"]:
            c.drawString(margin, y_position, item["DescripcionItem"])
            c.drawString(margin + 7 * cm, y_position, str(item["CantidadUnidadesItem"]))
            c.drawString(margin + 10 * cm, y_position, f"S/{item['precioUnitario']:.2f}")
            c.drawString(margin + 13 * cm, y_position, f"S/{item['totalValorVenta']:.2f}")
            y_position -= item_height

        # Totals
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

        # Add Hash Code
        y_position -= 2 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, 100, f"Hash Code: {hash_code}")

        # Generate QR Code
        qr_data = f"{data['emisor']['DocumentoEmisor']}|{data['comprobante']['tipoComprobante']}|{data['comprobante']['serieDocumento']}|{data['comprobante']['numeroDocumento']}|{data['comprobante']['totalConImpuestos']}|{data['comprobante']['fechaEmision']}|{hash_code}"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Draw QR Code using ImageReader
        y_position -= 7.5 * cm  # Adjust the position for the QR code
        qr_x_position = margin
        qr_image = ImageReader(buffer)
        c.drawImage(qr_image, qr_x_position, y_position, 6 * cm, 6 * cm)

        c.save()
        file_url = f'http://localhost:8001/{file_path}'
        return JsonResponse({'pdf_url': file_url})

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)})
