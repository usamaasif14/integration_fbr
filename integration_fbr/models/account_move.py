from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for move in self:
            if move.move_type == 'out_invoice':
                self.env['fbr.integration.model'].create_from_move(move)
        return res 