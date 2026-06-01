from odoo import models, fields, api

#1. NUEVO MODELO: Para el personal asignado
class MaintenanceRequestWorker(models.Model):
    _name = 'maintenance.request.worker'
    _description = 'Personal Asignado al Mantenimiento'

    request_id = fields.Many2one('maintenance.request', string='Solicitud', ondelete='cascade')
    
    # Vinculamos con los empleados de Odoo
    employee_id = fields.Many2one('hr.employee', string='Encargado', required=True)
    
    # Este campo trae automáticamente el cargo del empleado (si lo tiene en Odoo), 
    # pero permite borrarlo y escribir uno distinto de forma manual solo para este trabajo.
    job_title = fields.Char(string='Cargo')
    
    # Usamos onchange para que cuando selecciones al empleado, Odoo copie automáticamente su cargo
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                # Copiamos directamente el campo de texto nativo del empleado
                record.job_title = record.employee_id.job_title
            else:
                record.job_title = False

class MaintenanceRequestPhoto(models.Model):
    _name = 'maintenance.request.photo'
    _description = 'Registro Fotográfico de Mantenimiento'
    _order = 'equipment_id, mars_sequence'

    request_id = fields.Many2one('maintenance.request', string='Solicitud', ondelete='cascade')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipo')
    
    # Nuevo campo para la numeración 1., 2., 3.
    mars_sequence = fields.Integer(string='N°', compute='_compute_mars_sequence', store=True)
    
    image = fields.Image(string='Fotografía', required=True)
    subtitle = fields.Char(string='Subtítulo / Descripción')
    photo_type = fields.Selection([
        ('general', 'General'),
        ('acta', 'Acta de Conformidad'),
        ('gancho', 'Inspección de Gancho')
    ], string='Tipo de Foto', default='general')

    @api.depends('request_id.mars_photo_ids.equipment_id')
    def _compute_mars_sequence(self):
        for request in self.mapped('request_id'):
            # Creamos un diccionario para llevar la cuenta de cada equipo por separado
            counters = {}
            for photo in request.mars_photo_ids:
                if photo.equipment_id:
                    # Obtenemos el ID del equipo y le sumamos 1 a su contador
                    eq_id = photo.equipment_id.id
                    counters[eq_id] = counters.get(eq_id, 0) + 1
                    photo.mars_sequence = counters[eq_id]
                else:
                    photo.mars_sequence = 0

# NUEVO MODELO: Para las Tablas de Medidas Eléctricas
class MaintenanceRequestElectricalData(models.Model):
    _name = 'maintenance.request.electrical.data'
    _description = 'Medidas Eléctricas por Equipo'

    request_id = fields.Many2one('maintenance.request', string='Solicitud', ondelete='cascade')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipo', required=True)

    # Bloque 1: Tensión de Alimentación
    tension_nominal = fields.Char(string='Valor (V)', default='440')
    tension_l1_l2 = fields.Float(string='Valores L1-L2 (V)')
    tension_l1_l3 = fields.Float(string='Valores L1-L3 (V)')
    tension_l2_l3 = fields.Float(string='Valores L2-L3 (V)')

    # Bloque 2: Medidas de Corriente
    corriente_datos = fields.Char(string='Datos', default='IZQ/DERECHA')
    corriente_l1 = fields.Float(string='Valores L1 (A)')
    corriente_l2 = fields.Float(string='Valores L2 (A)')
    corriente_l3 = fields.Float(string='Valores L3 (A)')

    # NUEVO: Candado de base de datos para evitar duplicados
    _sql_constraints = [
        ('unique_request_equipment', 
         'UNIQUE(request_id, equipment_id)', 
         '¡Este equipo ya tiene una tabla de medidas asignada en esta solicitud!')
    ]

# CREAMOS EL NUEVO MODELO PARA LA LISTA DE REPUESTOS
class MarsMaintenancePart(models.Model):
    _name = 'mars.maintenance.part'
    _description = 'Repuestos Utilizados'

    maintenance_id = fields.Many2one('maintenance.request', string='Mantenimiento')
    name = fields.Char(string='Descripción del Repuesto', required=True)
    quantity = fields.Float(string='Cantidad', default=1.0)

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    # 1. Sobreescribimos el campo nativo para que sea de solo lectura y tenga 'Nuevo' por defecto
    name = fields.Char(string='Solicitud', default='Nuevo', copy=False, readonly=True)
    
    # 2. Creamos el nuevo campo para el título de la solicitud
    mars_title = fields.Char(string='Título de la solicitud', required=True)

    # Campo Many2many para soportar múltiples equipos
    mars_equipment_ids = fields.Many2many(
        'maintenance.equipment',
        string='Equipos',
        help='Selecciona uno o varios equipos para esta solicitud.'
    )

    # NUEVOS CAMPOS: Datos de Certificación / Inspección
    mars_oc = fields.Char(string='OC')
    mars_item = fields.Char(string='ITEM')
    mars_emission_date = fields.Date(string='Fecha de Emisión', default=fields.Date.context_today)
    mars_inspector = fields.Char(string='Inspector')
    mars_client_id = fields.Many2one('res.partner', string='Cliente')
    mars_applicable_norm = fields.Char(string='Norma Aplicable', default='ASME B30.16 - B30.10')
    mars_diagnosis = fields.Char(string='Diagnóstico')

    # --- NUEVOS CAMPOS PARA LA PÁGINA 2 ---
    maintenance_type = fields.Selection(
        selection_add=[
            ('overhaul', 'Overhaul'),
            ('inspective', 'Inspectivo'),
            ('predictive', 'Predictivo'),
        ],
        ondelete={
            'overhaul': 'set default',
            'inspective': 'set default',
            'predictive': 'set default',
        }
    )

    mars_execution_date = fields.Date(string='Fecha de Ejecución', default=fields.Date.context_today)

    # Relaciones one2many para el personal asignado y las fotos
    mars_worker_ids = fields.One2many(
        'maintenance.request.worker', 
        'request_id', 
        string='Personal Asignado'
    )

    mars_conclusions = fields.Html(
        string='Conclusiones', 
        help='Registre las conclusiones detalladas, recomendaciones o hallazgos del mantenimiento.'
    )

# 1. Sección Acta de Conformidad (Filtrada)
    mars_acta_ids = fields.One2many(
        'maintenance.request.photo', 'request_id', 
        string='Fotos Acta de Conformidad',
        domain=[('photo_type', '=', 'acta')]
    )

    # 2. Sección Inspección de Gancho (Filtrada)
    mars_gancho_ids = fields.One2many(
        'maintenance.request.photo', 'request_id', 
        string='Fotos Inspección de Gancho',
        domain=[('photo_type', '=', 'gancho')]
    )

    # Relación con el nuevo modelo de fotos
    mars_photo_ids = fields.One2many(
        'maintenance.request.photo',
        'request_id',
        string='Registro Fotográfico',
        domain=[('photo_type', '=', 'general')]
    )

    # NUEVO: Numeración en tiempo real para las fotos
    @api.onchange('mars_photo_ids')
    def _onchange_mars_photo_ids_sequence(self):
        for request in self:
            counters = {}
            for photo in request.mars_photo_ids:
                if photo.equipment_id:
                    # Obtenemos el ID del equipo en memoria
                    eq_id = photo.equipment_id.id
                    # Sumamos 1 al contador de ese equipo específico
                    counters[eq_id] = counters.get(eq_id, 0) + 1
                    # Le asignamos ese número a la foto
                    photo.mars_sequence = counters[eq_id]


    # 3. Lógica para generar el correlativo al crear un nuevo registro
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si el nombre es 'Nuevo' (o no tiene), le asignamos la secuencia
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.request.mars') or 'Nuevo'
        
        # Llamamos al método create original (super) para que guarde en base de datos
        return super(MaintenanceRequest, self).create(vals_list)
    
    
    # NUEVO CAMPO: Conexión a las tablas eléctricas
    mars_electrical_ids = fields.One2many(
        'maintenance.request.electrical.data',
        'request_id',
        string='Tablas de Medidas Eléctricas'
    )

    # NUEVO: Campo "invisible" que calcula qué equipos aún están disponibles
    mars_available_equipment_ids = fields.Many2many(
        'maintenance.equipment',
        compute='_compute_mars_available_equipment'
    )

    # Función que hace el cálculo automático
    @api.depends('mars_equipment_ids', 'mars_electrical_ids.equipment_id')
    def _compute_mars_available_equipment(self):
        for request in self:
            # Detectamos qué equipos YA están en las filas de las medidas eléctricas
            used_ids = request.mars_electrical_ids.mapped('equipment_id').ids
            
            # Dejamos disponibles solo los equipos que NO están en la lista de usados
            request.mars_available_equipment_ids = request.mars_equipment_ids.filtered(
                lambda eq: eq.id not in used_ids
            )

    # AUTOMATIZACIÓN: Generar tablas según los equipos
    @api.onchange('mars_equipment_ids')
    def _onchange_sync_electrical_tables(self):
        for record in self:
            # Obtenemos los IDs de los equipos que ya tienen tabla y los que están seleccionados
            existing_equip_ids = record.mars_electrical_ids.mapped('equipment_id.id')
            selected_equip_ids = record.mars_equipment_ids.ids

            commands = []
            
            # Crear una tabla nueva por cada equipo seleccionado que aún no la tenga
            for equip_id in selected_equip_ids:
                if equip_id not in existing_equip_ids:
                    commands.append((0, 0, {
                        'equipment_id': equip_id,
                        'tension_nominal': '440',
                        'corriente_datos': 'IZQ/DERECHA'
                    }))
                    
            # Eliminar la tabla si el usuario quita un equipo de la solicitud
            for line in record.mars_electrical_ids:
                if line.equipment_id.id not in selected_equip_ids and line.id:
                    commands.append((2, line.id, 0))
                # Manejo especial para líneas nuevas en memoria que aún no se han guardado
                elif line.equipment_id.id not in selected_equip_ids and not line.id:
                    commands.append((3, line.id, 0))
                    
            if commands:
                record.mars_electrical_ids = commands


    # Campos para el Certificado del Inspector
    mars_inspector_certificate = fields.Binary(string='Certificado del Inspector', attachment=True)
    mars_inspector_certificate_name = fields.Char(string='Nombre del Certificado')

    # Nuevos campos para Observaciones y Repuestos
    mars_final_observations = fields.Text(string='Observaciones Finales')
    mars_used_parts = fields.Boolean(string='¿Se utilizaron repuestos?', default=False)
    
    # Relación con la tabla de repuestos
    mars_part_ids = fields.One2many(
        'mars.maintenance.part', 
        'maintenance_id', 
        string='Lista de Repuestos'
    )