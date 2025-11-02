from odoo import api, models
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _inherit = "estate.property.offer"

    @api.model
    def create(self, vals):
        property_obj = self.env['estate.property'].browse(vals.get('property_id'))

        property_obj.state = 'offer_received'

        existing_offers = property_obj.offer_ids.mapped('price')
        if existing_offers and vals.get('price') < max(existing_offers):
            raise UserError("Offer price must be higher than existing offers.")

        return super().create(vals)
