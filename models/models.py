# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LibroLRE(models.Model):
    _inherit = 'hr.contract'

    region_id = fields.Many2one(comodel_name='hr.tabla_lre', string='Región Trabajo',domain="[('tipo_tabla','=','region')]")
    causal_despido_id = fields.Many2one(comodel_name='hr.tabla_lre', string='Causal Término Contrato',domain="[('tipo_tabla','=','causal_despido')]")
    comuna_id = fields.Many2one(comodel_name='res.country.state', string='Comuna Trabajo')
    jornada_id = fields.Many2one(comodel_name='hr.tabla_lre', string='Tipo Jornada',domain="[('tipo_tabla','=','tipo_jornada')]")
    impuesto_id = fields.Many2one(comodel_name='hr.tabla_lre', string='Tipo Impuesto',domain="[('tipo_tabla','=','tipo_impuesto')]")
    tecnico_extranjero = fields.Selection(string='Tecnico Extranjero', selection=[('0', 'NO'), ('1', 'SI'),])
    persona_discapacidad = fields.Selection(string='Persona con Discapacidad', 
                            selection=[('0', 'NO'), 
                            ('1', 'Discapacidad Certificada por la Compin'),
                            ('2', 'Asignatario Pensión por Invalidez Total'),
                            ('3', 'Pensionado con Invalidez Parcial'),
                            ])
    pensionado_vejez = fields.Selection(string='Pensionado Vejez', selection=[('0', 'NO'), ('1', 'SI'),])
    ips_id = fields.Many2one(comodel_name='hr.tabla_lre', string='IPS',domain="[('tipo_tabla','=','ips')]")    
    tramo_asig_fam = fields.Selection(string='Tramo Asignación Familiar',
                                     selection=[('A', 'Primer Tramo'), 
                                     ('B', 'Segundo Tramo'),
                                     ('C', 'Tercer Tramo'),
                                     ('D', 'Sin Derecho'),
                                     ('S', 'Sin Información'),
                                     ])
    afc = fields.Selection(string='Afc', selection=[('0', 'NO'), ('1', 'SI'),])


class Afp(models.Model):
    _inherit = 'hr.afp'

    codigo_lre = fields.Selection(string='Código LRE', 
                selection=[('100', 'No Esta En Afp'), 
                            ('6', 'Provida'),
                            ('11', 'Plan Vital'),
                            ('13', 'Cuprum'),
                            ('14', 'Habitat'),
                            ('19', 'Uno'),
                            ('31', 'Capital'),
                            ('103', 'Modelo'),
                            ])

class Isapre(models.Model):
    _inherit = 'hr.isapre'

    codigo_lre = fields.Selection(string='Código LRE', 
                selection=[('102', 'Fonasa'), 
                            ('1', 'Cruz Blanca'),
                            ('3', 'Banmedica'),
                            ('4', 'Colmena'),
                            ('9', 'Consalud'),
                            ('12', 'Vida Tres'),
                            ('37', 'Chuquicamata'),
                            ('38', 'Cruz Del Norte'),
                            ('39', 'Fusat'),
                            ('40', 'Fundación (Banco Estado)'),
                            ('41', 'Rio Blanco'),
                            ('42', 'San Lorenzo'),
                            ('43', 'Nueva Mas Vida'),
                            ])

class CCAF(models.Model):
    _inherit = 'hr.ccaf'

    codigo_lre = fields.Selection(string='Código LRE', 
                selection=[('0', 'No'), 
                            ('1', 'Los Andes'),
                            ('2', 'La Araucana'),
                            ('3', 'Los Héroes'),
                            ('4', '18 de Septiembre'),
                            ])

class Mutual(models.Model):
    _inherit = 'hr.mutual'

    codigo_lre = fields.Selection(string='Código LRE', 
                selection=[('0', 'Sin Mutual de Seguridad'), 
                            ('1', 'Asociación Chilena de Seguridad (ACHS)'),
                            ('2', 'Mutual de Seguridad CCHC'),
                            ('3', 'Instituto de Seguridad del Trabajo (IST)'),
                            ])
    
    
