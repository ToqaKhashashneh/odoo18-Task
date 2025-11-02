from odoo import api, fields, models
from datetime import timedelta, date
from odoo.exceptions import ValidationError, UserError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"


    # =========================
    # Fields
    # =========================
    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    postcode = fields.Char()
    availability_date = fields.Date(
        copy=False,
        default=lambda self: date.today() + timedelta(days=90)
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        [('north', 'North'),
         ('south', 'South'),
         ('east', 'East'),
         ('west', 'West')],
        string="Garden Orientation"
    )
    total_area = fields.Float(
        string="Total Area (sqm)",
        compute="_compute_total_area"
    )

    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled'),
        ],
        string="Status",
        required=True,
        copy=False,
        default='new',
    )

    best_price = fields.Float(
        string="Best Offer",
        compute="_compute_best_price"
    )

    # =========================
    # Relations
    # =========================
    salesperson_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )
    buyer_id = fields.Many2one(
        "res.partner", string="Buyer", copy=False
    )
    property_type_id = fields.Many2one(
        "estate.property.type", string="Property Type"
    )
    tag_ids = fields.Many2many(
        "estate.property.tag",
        string="Tags"
    )
    offer_ids = fields.One2many(
        "estate.property.offer",
        "property_id",
        string="Offers"
    )

    # =========================
    # Compute Methods
    # =========================
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = (record.living_area or 0) + (record.garden_area or 0)

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped("price"))
            else:
                record.best_price = 0.0

    # =========================
    # Onchange
    # =========================
    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # =========================
    # Actions
    # =========================
    def action_sold(self):
        for record in self:
            if record.state == "cancelled":
                raise UserError("Canceled properties cannot be sold.")
            record.state = "sold"
        return True

    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("Sold properties cannot be cancelled.")
            record.state = "cancelled"
        return True

    # =========================
    # Constraints
    # =========================
    _sql_constraints = [
        ('check_expected_price_positive',
         'CHECK(expected_price > 0)',
         "Expected price must be strictly positive."),
        ('check_selling_price_positive',
         'CHECK(selling_price >= 0)',
         "Selling price must be positive."),
        ('unique_property_name',
         'UNIQUE(name)',
         "The property name must be unique."),
    ]

    @api.constrains("selling_price", "expected_price")
    def _check_selling_price(self):
        for record in self:
            if record.selling_price and record.selling_price < 0.9 * record.expected_price:
                raise ValidationError("Selling price cannot be lower than 90% of the expected price.")

    # =========================

class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Type"
    _order = "sequence, name"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=1)
    property_ids = fields.One2many("estate.property", "property_type_id", string="Properties")

    offer_ids = fields.One2many("estate.property.offer", "property_type_id", string="Offers")
    offer_count = fields.Integer(compute="_compute_offer_count")
    has_offers = fields.Boolean(compute="_compute_has_offers")

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.depends("offer_ids")
    def _compute_has_offers(self):
        for record in self:
            record.has_offers = bool(record.offer_ids)

    def action_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offers',
            'res_model': 'estate.property.offer',
            'view_mode': 'list,form',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id},
        }

    _sql_constraints = [
        ('unique_property_type_name',
         'UNIQUE(name)',
         "The property type name must be unique."),
    ]

    # =========================

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Property Tag"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color")

    _sql_constraints = [
        ('unique_property_tag_name',
         'UNIQUE(name)',
         "The property tag name must be unique."),
    ]

    # =========================

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc"

    price = fields.Float(string="Price")
    status = fields.Selection(
        [
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        string="Status",
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)

    # Related field to property_type
    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Property Type",
        related="property_id.property_type_id",
        store=True
    )
    _sql_constraints = [
        ('check_offer_price_positive',
         'CHECK(price > 0)',
         "Offer price must be strictly positive."),
    ]

    