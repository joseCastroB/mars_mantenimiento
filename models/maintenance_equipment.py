from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Campos personalizados para MARS
    mars_marca = fields.Char(string='Marca')
    mars_capacidad = fields.Char(string='Capacidad')
    mars_ramales = fields.Char(string='Ramales')
    mars_voltaje_fuerza = fields.Char(string='Voltaje de Fuerza')
    mars_tipo_alimentacion = fields.Char(string='Tipo de Alimentación')
    mars_tipo_control = fields.Char(string='Tipo de Control')
    
    # Campo para la foto de la placa
    mars_placa_imagen = fields.Image(
        string='Foto de la Placa', 
        max_width=1920, 
        max_height=1920,
        help="Sube una fotografía de la placa técnica del equipo."
    )