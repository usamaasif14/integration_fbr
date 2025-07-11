import requests
from odoo import models, fields, api
import base64
import qrcode
from io import BytesIO

class FBRIntegrationModel(models.Model):
    _name = 'fbr.integration.model'
    _description = 'FBR Integration Model'
    _order = 'id desc'

    move_id = fields.Many2one('account.move', string='Original Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    amount_total = fields.Monetary(string='Total Amount', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    invoice_line_ids = fields.One2many('fbr.integration.line', 'fbr_invoice_id', string='Invoice Lines', readonly=True)
    qr_code = fields.Binary(string='QR Code', readonly=True)
    fbr_status = fields.Char(string='FBR Status', readonly=True)
    fbr_response = fields.Text(string='FBR Response', readonly=True)

    def action_send_to_fbr(self):
        """Send invoice data to FBR demo API and store the response."""
        for rec in self:
            move = rec.move_id if rec.move_id else False
            partner = rec.partner_id if rec.partner_id else False
            payload = [
                {
                    "MerchantId": "PayProUser",  # Demo credentials
                    "MerchantPassword": "Password"
                },
                {
                    "OrderNumber": getattr(move, 'name', '') or getattr(move, 'id', ''),
                    "OrderAmount": str(rec.amount_total),
                    "OrderDueDate": rec.invoice_date.strftime('%d/%m/%Y') if rec.invoice_date else '',
                    "OrderType": "Service",
                    "IssueDate": rec.invoice_date.strftime('%d/%m/%Y') if rec.invoice_date else '',
                    "CustomerName": getattr(partner, 'name', ''),
                    "CustomerMobile": getattr(partner, 'mobile', ''),
                    "CustomerEmail": getattr(partner, 'email', ''),
                    "CustomerAddress": getattr(partner, 'contact_address', ''),
                }
            ]
            url = "https://demoapi.paypro.com.pk/cpay/co?oJson="
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    resp_json = response.json()
                    status = resp_json[0].get('Status', '')
                    rec.fbr_status = 'Success' if status == '00' else 'Failed'
                    rec.fbr_response = str(resp_json)
                else:
                    rec.fbr_status = 'HTTP Error'
                    rec.fbr_response = response.text
            except Exception as e:
                rec.fbr_status = 'Error'
                rec.fbr_response = str(e)

    @api.model
    def create_from_move(self, move):
        lines = []
        for line in move.invoice_line_ids:
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
            }))
        qr_data = f"Invoice: {move.name}, Amount: {move.amount_total}, Date: {move.invoice_date}"
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer)  # qrcode's save() does not need 'format' if using PNG
        qr_code = base64.b64encode(buffer.getvalue()).decode('utf-8')
        rec = self.create([{
            'move_id': move.id,
            'partner_id': move.partner_id.id,
            'invoice_date': move.invoice_date,
            'amount_total': move.amount_total,
            'currency_id': move.currency_id.id,
            'invoice_line_ids': lines,
            'qr_code': qr_code,
        }])[0]
        # Optionally, send to FBR automatically here:
        # rec.action_send_to_fbr()
        return rec

class FBRIntegrationLine(models.Model):
    _name = 'fbr.integration.line'
    _description = 'FBR Integration Invoice Line'

    fbr_invoice_id = fields.Many2one('fbr.integration.model', string='FBR Invoice', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    name = fields.Char(string='Description', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    price_unit = fields.Float(string='Unit Price', readonly=True)
    price_subtotal = fields.Float(string='Subtotal', readonly=True) 