# apps/reports/utils.py

def format_sale_details_for_csv(sale_details):
    """
    Toma los detalles de una venta y los concatena en una sola string
    para ser mostrada en la columna 'Detalle_Productos' del CSV.
    """
    return "; ".join([
        f"{detail.product.name} ({detail.quantity}x)" 
        for detail in sale_details
    ])