{
    'name': 'MARS Mantenimiento',
    'version': '1.0',
    'summary': 'Personalización del módulo de mantenimiento para Corporación MARS',
    'description': 'Añade campos técnicos específicos y fotografía de placa a los equipos de mantenimiento.',
    'category': 'Maintenance',
    'author': 'Jose Castro',
    'depends': ['maintenance', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
        'views/maintenance_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}