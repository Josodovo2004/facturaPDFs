from django.urls import path
from .views import (
    create_pdf_comprobante
)

urlpatterns = [
    path('create_pdf_comprobante/', create_pdf_comprobante, name='create_pdf_comprobante'),
]
