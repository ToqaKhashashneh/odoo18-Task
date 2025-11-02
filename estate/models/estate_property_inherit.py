from odoo import models, api
from odoo.exceptions import UserError

class EstateProperty(models.Model):
    _inherit = "estate.property"

    @api.ondelete(at_uninstall=False)
    def _check_state_before_delete(self):
        for record in self:
            if record.state not in ("new", "cancelled"):
                raise UserError("You can only delete properties that are New or Cancelled.")
