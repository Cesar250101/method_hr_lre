from odoo import api, fields, models, tools, _


class hr_causal_despido(models.Model):
    _name = 'hr.tabla_lre'
    _description = 'Causales de despido'

    tipo_tabla = fields.Selection(string='Tipos de Tabla', 
                                selection=[('causal_despido', 'Causal Despido'), 
                                ('region', 'Región de Prestación de Servicios'),
                                ('tipo_jornada', 'Tipo Jornada'),
                                ('tipo_impuesto', 'Tipo Impuesto'),
                                ('ips', 'IPS (Ex INP)'),
                                ])  

    codigo = fields.Integer('Codigo', required=True)
    name = fields.Char('Nombre', required=True)



class Comunas(models.Model):
    _inherit = 'res.country.state'

    lre_codigo = fields.Char(string='Código Comuna lre')

    
    
