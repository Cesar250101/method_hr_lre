
import io
import csv
import base64
import logging
import time
from datetime import datetime
from dateutil import relativedelta

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class WizardExportCsvLre(models.TransientModel):

    _name = 'wizard.export.csv.lre'
    _description = 'wizard.export.csv.lre'
    
    delimiter = {
        'comma':  ',',
        'dot_coma':  ';',
        'tab':  '\t',
    }
    quotechar = {
        'colon':  '"',
        'semicolon':  "'",
        'none':  '',
    } 
    
    date_from = fields.Date('Fecha Inicial', required=True, default=lambda self: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Fecha Final', required=True, default=lambda self: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    file_data = fields.Binary('Archivo Generado')
    file_name = fields.Char('Nombre de archivo')
    delimiter_option = fields.Selection([
        ('colon','Comillas Dobles(")'),
        ('semicolon',"Comillas Simples(')"),
        ('none',"Ninguno"),
        ], string='Separador de Texto', default='colon', required=True)
    delimiter_field_option = fields.Selection([
        ('comma','Coma(,)'),
        ('dot_coma',"Punto y coma(;)"),
        ('tab',"Tabulador"),
        ], string='Separador de Campos', default='dot_coma', required=True)
    
    @api.multi
    def show_view(self, name):
        search_ids = self.env['wizard.export.csv.lre'].search([])
        last_id = search_ids and max(search_ids)        
        return {
            'name': name,
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.export.csv.lre',
            'res_id': last_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def get_nacionalidad(self, employee):
        #0 chileno, 1 extranjero, comparar con el pais de la compañia
        if employee == 46:
            return 0
        else:
            return 1
        
    @api.model
    def get_tipo_pago(self, employee):
        #01 Remuneraciones del mes
        #02 Gratificaciones
        #03 Bono Ley de Modernizacion Empresas Publicas
        #TODO: en base a que se elije el tipo de pago???
        return 1
    
    @api.model
    def get_regimen_provisional(self, contract):
        if contract.pension is True:
            return 'SIP'
        else:
            return 'AFP'
    
    @api.model
    def get_tipo_trabajador(self, employee):

        if employee.type_id is False:
            return 0
        else:
            tipo_trabajador = employee.type_id.id_type

        #Codigo    Glosa
        #id_type
        #0        Activo (No Pensionado)
        #1        Pensionado y cotiza
        #2        Pensionado y no cotiza
        #3        Activo > 65 años (nunca pensionado)
        return tipo_trabajador
    
    @api.model
    def get_dias_trabajados(self, payslip):
        worked_days = 0
        if payslip:
            for line in payslip.worked_days_line_ids:
                    if line.code == 'WORK100':
                        worked_days = line.number_of_days
        return worked_days

    @api.model
    def get_cost_center(self, contract):
        cost_center = "1"
        if contract.analytic_account_id:
            cost_center = contract.analytic_account_id.code
        return cost_center


    @api.model
    def get_tipo_linea(self, payslip):
        #00 Linea Principal o Base
        #01 Linea Adicional
        #02 Segundo Contrato
        #03 Movimiento de Personal Afiliado Voluntario
        return '00'


    @api.model
    def get_tramo_asignacion_familiar(self, payslip, valor):
        try:
            if payslip.contract_id.carga_familiar != 0 and payslip.indicadores_id.asignacion_familiar_tercer >= payslip.contract_id.wage and payslip.contract_id.pension is False:
                if payslip.indicadores_id.asignacion_familiar_primer >= valor:
                    return 'A'
                elif payslip.indicadores_id.asignacion_familiar_segundo  >= valor:
                    return 'B'
                elif payslip.indicadores_id.asignacion_familiar_tercer  >= valor:
                    return 'C'
            else:
                return 'D' 
        except:
            return 'D' 
            
    
    def get_payslip_lines_value(self, obj, regla):
        try:
            linea = obj.search([('code','=',regla)])
            valor = linea.amount
            return valor 
        except:
            return '0' 

    def get_payslip_lines_value_2(self, obj, regla):
        valor = 0
        lineas = self.env['hr.payslip.line']
        detalle = lineas.search([('slip_id','=',obj.id),('code','=',regla)])
        valor = detalle.amount
        return valor        

    def get_payslip_lines_value_nombre(self, obj, nombre):
        valor = 0
        lineas = self.env['hr.payslip.line']
        detalle = lineas.search([('slip_id','=',obj.id),('name','ilike',nombre)])
        for d in detalle:
            valor += d.amount
        return valor        


    @api.model
    def get_imponible_afp(self, payslip, TOTIM):
        if payslip.contract_id.pension is True:
            return '0'
        elif TOTIM >=round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf):
            return round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf)
        else:
            return round(TOTIM)

    @api.model
    def get_imponible_afp_2(self, payslip, TOTIM, LIC):
        if LIC > 0:
            TOTIM=LIC
        if payslip.contract_id.pension is True:
            return '0'
        elif TOTIM >=round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf):
            return int(round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf))      
        else:
            return int(round(TOTIM))

    @api.model
    def get_imponible_mutual(self, payslip, TOTIM):
        if payslip.contract_id.mutual_seguridad is False:
            return 0
        elif payslip.contract_id.type_id.name == 'Sueldo Empresarial':
            return 0 
        elif TOTIM >=round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf):
            return round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf)
        else:
            return round(TOTIM)    

    @api.model
    def get_imponible_seguro_cesantia(self, payslip, TOTIM, LIC):
        if LIC > 0:
            TOTIM=LIC
        if payslip.contract_id.pension is True:
            return 0
        elif payslip.contract_id.type_id.name == 'Sueldo Empresarial':
            return 0
        elif TOTIM >=round(payslip.indicadores_id.tope_imponible_seguro_cesantia*payslip.indicadores_id.uf):
            return int(round(payslip.indicadores_id.tope_imponible_seguro_cesantia*payslip.indicadores_id.uf))
        else:
            return int(round(TOTIM))

    @api.model
    def get_imponible_salud(self, payslip, TOTIM):
        result = 0
        if TOTIM >= round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf):
            return int(round(payslip.indicadores_id.tope_imponible_afp*payslip.indicadores_id.uf))
        else:
            return int(round(TOTIM))

    @api.model
    def _acortar_str(self, texto, size=1):
        c = 0
        cadena = ""
        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        return cadena


    @api.model
    def _arregla_str(self, texto, size=1):
        c = 0
        cadena = ""
        special_chars = [
         ['á', 'a'],
         ['é', 'e'],
         ['í', 'i'],
         ['ó', 'o'],
         ['ú', 'u'],
         ['ñ', 'n'],
         ['Á', 'A'],
         ['É', 'E'],
         ['Í', 'I'],
         ['Ó', 'O'],
         ['Ú', 'U'],
         ['Ñ', 'N']]

        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        for char in special_chars:
            try:
                cadena = cadena.replace(char[0], char[1])
            except:
                pass
        return cadena
    
    @api.multi
    def action_generate_csv(self):
        employee_model = self.env['hr.employee']
        payslip_model = self.env['hr.payslip']
        payslip_line_model = self.env['hr.payslip.line']       
        sexo_data = {'male': "M",
                     'female': "F",
                     }
        _logger = logging.getLogger(__name__)
        country_company = self.env.user.company_id.country_id
        output = io.StringIO()
        if self.delimiter_option == 'none':
            writer = csv.writer(output, delimiter=self.delimiter[self.delimiter_field_option], quoting=csv.QUOTE_NONE)
        else:
            writer = csv.writer(output, delimiter=self.delimiter[self.delimiter_field_option], quotechar=self.quotechar[self.delimiter_option], quoting=csv.QUOTE_NONE)
        #Debemos colocar que tome todo el mes y no solo el día exacto TODO
        payslip_recs = payslip_model.search([('date_from','=',self.date_from),
                                             ])

        date_start = self.date_from
        date_stop = self.date_to
        date_start_format = date_start.strftime("%m%Y")
        date_stop_format = date_stop.strftime("%m%Y")
        line_employee = []
        rut = ""
        rut_dv = ""
        rut_emp = ""
        rut_emp_dv = ""

        try:
            rut_emp, rut_emp_dv = self.env.user.company_id.vat.split("-")
            rut_emp = rut_emp.replace('.','')
        except:
            pass  

        line_employee_encabezados = ['1101-Rut trabajador',
                    '1102-Fecha inicio contrato',
                    '1103-Fecha de término de contrato',
                    '1104-Causal de término del contrato',
                    '1105-Región de prestación de los servicios',
                    '1106-Comuna de prestación de los servicios',
                    '1170-Tipo de impuesto a la renta',
                    '1146-Técnico extranjero exención de cotizaciones previsionales (ley 18.156)',
                    '1107-Código tipo de jornada',
                    '1108-Persona con discapacidad/pensionado por invalidez',
                    '1109-Pensionado por vejez',
                    '1141-AFP',
                    '1142-IPS (ExINP)',
                    '1143-FONASA / ISAPRE',
                    '1151-AFC',
                    '1110-CCAF',
                    '1152-Org. administrador ley 16.744',
                    '1111-Número cargas familiares legales autorizadas',
                    '1112-Número de cargas familiares maternales',
                    '1113-Número de cargas familiares invalidez',
                    '1114-Tramo asignación familiar',
                    '1171-Rut organización sindical 1',
                    '1172-Rut organización sindical 2',
                    '1173-Rut organización sindical 3',
                    '1174-Rut organización sindical 4',
                    '1175-Rut organización sindical 5',
                    '1176-Rut organización sindical 6',
                    '1177-Rut organización sindical 7',
                    '1178-Rut organización sindical 8',
                    '1179-Rut organización sindical 9',
                    '1180-Rut organización sindical 10',
                    '1115-Número días trabajados en el mes',
                    '1116-Número días de licencia médica en el mes',
                    '1117-Número días de vacaciones en el mes',
                    '1118-Subsidio trabajador joven',
                    '1154-Puesto trabajo pesado',
                    '1155-Ahorro previsional voluntario individual',
                    '1157-Ahorro previsional voluntario colectivo',
                    '1131-Indemnización a todo evento (Art. 164)',
                    '1132-Tasa indemnización a todo evento (Art. 164)',
                    '2101-Sueldo',
                    '2102-Sobresueldo',
                    '2103-Comisiones (mensual)',
                    '2104-Semana corrida mensual (Art. 45)',
                    '2105-Participación (mensual)',
                    '2106-Gratificación (mensual)',
                    '2107-Recargo 30% día domingo (Art. 38)',
                    '2108-Remuneración variable pagada en vacaciones (Art. 71)',
                    '2109-Remuneración variable pagada en clausura (Art. 38 DFL 2)',
                    '2110-Aguinaldo',
                    '2111-Bonos u otras remuneraciones fijas mensuales',
                    '2112-Tratos (mensual)',
                    '2113-Bonos u otras remuneraciones variables mensuales o superiores a un mes',
                    '2114-Ejercicio opción no pactada en contrato (Art. 17 N°8 LIR)',
                    '2115-Beneficios en especie constitutivos de remuneración',
                    '2116-Remuneraciones bimestrales (devengo en dos meses)',
                    '2117-Remuneraciones trimestrales (devengo en tres meses)',
                    '2118-Remuneraciones cuatrimestral (devengo en cuatro meses)',
                    '2119-Remuneraciones semestrales (devengo en seis meses)',
                    '2120-Remuneraciones anuales (devengo en doce meses)',
                    '2121-Participación anual (devengo en doce meses)',
                    '2122-Gratificación anual (devengo en doce meses)',
                    '2123-Otras remuneraciones superiores a un mes',
                    '2124-Pago por horas de trabajo sindical',
                    '2161-Sueldo empresarial',
                    '2201-Subsidio por incapacidad laboral por licencia médica - total mensual',
                    '2202-Beca de estudio (Art. 17 N°18 LIR)',
                    '2203-Gratificaciones de zona (Art. 17 N°27)',
                    '2204-Otros ingresos no constitutivos de renta (Art. 17 N°29 LIR)',
                    '2301-Colación total mensual (Art. 41)',
                    '2302-Movilización total mensual (Art. 41)',
                    '2303-Viáticos total mensual (Art. 41)',
                    '2304-Asignación de pérdida de caja total mensual (Art. 41)',
                    '2305-Asignación de desgaste herramienta total mensual (Art. 41)',
                    '2311-Asignación familiar legal total mensual (Art. 41)',
                    '2306-Gastos por causa del trabajo (Art. 41)',
                    '2307-Gastos por cambio de residencia (Art. 53)',
                    '2308-Sala cuna (Art. 203)',
                    '2309-Asignación trabajo a distancia o teletrabajo',
                    '2347-Depósito convenido hasta UF 900',
                    '2310-Alojamiento por razones de trabajo (Art. 17 N°14 LIR)',
                    '2312-Asignación de traslación (Art. 17 N°15 LIR)',
                    '2313-Indemnización por feriado legal',
                    '2314-Indemnización años de servicio',
                    '2315-Indemnización sustitutiva del aviso previo',
                    '2316-Indemnización fuero maternal (Art. 163 bis)',
                    '2331-Indemnización a todo evento (Art. 164)',
                    '2417-Indemnizaciones voluntarias tributables',
                    '2418-Indemnizaciones contractuales tributables',
                    '3141-Cotización obligatoria previsional (AFP o IPS)',
                    '3143-Cotización obligatoria salud 7%',
                    '3144-Cotización voluntaria para salud',
                    '3151-Cotización AFC - trabajador',
                    '3146-Cotizaciones técnico extranjero para seguridad social fuera de Chile',
                    '3147-Descuento depósito convenido hasta UF 900 anual',
                    '3155-Cotización ahorro previsional voluntario individual modalidad A',
                    '3156-Cotización ahorro previsional voluntario individual modalidad B hasta UF 50',
                    '3157-Cotización ahorro previsional voluntario colectivo modalidad A',
                    '3158-Cotización ahorro previsional voluntario colectivo modalidad B hasta UF 50',
                    '3161-Impuesto retenido por remuneraciones',
                    '3162-Impuesto retenido por indemnizaciones',
                    '3163-Mayor retención de impuestos solicitada por el trabajador',
                    '3164-Impuesto retenido por reliquidación remuneraciones devengadas en otros períodos',
                    '3165-Diferencia de impuesto por reliquidación remuneraciones devengadas en este período',
                    '3166-Retención préstamo clase media 2020 (Ley 21.252)',
                    '3167-Rebaja zona extrema DL 889',
                    '3171-Cuota sindical 1',
                    '3172-Cuota sindical 2',
                    '3173-Cuota sindical 3',
                    '3174-Cuota sindical 4',
                    '3175-Cuota sindical 5',
                    '3176-Cuota sindical 6',
                    '3177-Cuota sindical 7',
                    '3178-Cuota sindical 8',
                    '3179-Cuota sindical 9',
                    '3180-Cuota sindical 10',
                    '3110-Crédito social CCAF',
                    '3181-Cuota vivienda o educación (Art. 58)',
                    '3182-Crédito cooperativas de ahorro (Art 54. Ley Coop.)',
                    '3183-Otros descuentos autorizados y solicitados por el trabajador',
                    '3154-Cotización adicional trabajo pesado - trabajador',
                    '3184-Donaciones culturales y de reconstrucción',
                    '3185-Otros descuentos (Art. 58)',
                    '3186-Pensiones de alimentos',
                    '3187-Descuento mujer casada (Art. 59)',
                    '3188-Descuentos por anticipos y préstamos',
                    '4151-Aporte AFC - empleador',
                    '4152-Aporte empleador seguro accidentes del trabajo y Ley SANNA (Ley 16.744)',
                    '4131-Aporte empleador indemnización a todo evento (Art. 164)',
                    '4154-Aporte adicional trabajo pesado - empleador',
                    '4155-Aporte empleador seguro invalidez y sobrevivencia',
                    '4157-Aporte empleador ahorro previsional voluntario colectivo',
                    '5201-Total haberes',
                    '5210-Total haberes imponibles y tributables',
                    '5220-Total haberes imponibles no tributables',
                    '5230-Total haberes no imponibles y no tributables',
                    '5240-Total haberes no imponibles y tributables',
                    '5301-Total descuentos',
                    '5361-Total descuentos impuestos a las remuneraciones',
                    '5362-Total descuentos impuestos por indemnizaciones',
                    '5341-Total descuentos por cotizaciones del trabajador',
                    '5302-Total otros descuentos',
                    '5410-Total aportes empleador',
                    '5501 Total líquido',
                    '5502-Total indemnizaciones',
                    '5564-Total indemnizaciones tributables',
                    '5565-total indemnizaciones no tributables',
                    ]
        writer.writerow([str(l) for l in line_employee_encabezados])
        for payslip in payslip_recs:
            payslip_line_recs = payslip_line_model.search([('slip_id','=',payslip.id)])
            rut = ""
            rut_dv = ""
            #rut, rut_dv = payslip.employee_id.identification_id.split("-")
            rut = payslip.employee_id.identification_id
            rut = rut.replace('.','')
            fecha_start=payslip.contract_id.date_start.strftime("%d-%m-%Y")
            if payslip.contract_id.date_end:
                fecha_end=payslip.contract_id.date_end.strftime("%d-%m-%Y")
            else:
                fecha_end=""
            line_employee = [self._acortar_str(rut, 11), 
                                fecha_start,
                                fecha_end,
                                payslip.contract_id.causal_despido_id.codigo,
                                payslip.contract_id.region_id.codigo,
                                payslip.contract_id.comuna_id.lre_codigo,
                                payslip.contract_id.impuesto_id.codigo,
                                payslip.contract_id.tecnico_extranjero,
                                payslip.contract_id.jornada_id.codigo,
                                payslip.contract_id.persona_discapacidad,
                                payslip.contract_id.pensionado_vejez,
                                payslip.contract_id.afp_id.codigo_lre,
                                payslip.contract_id.ips_id.codigo,
                                payslip.contract_id.isapre_id.codigo_lre,
                                payslip.contract_id.afc,
                                payslip.indicadores_id.ccaf_id.codigo_lre if payslip.indicadores_id.ccaf_id.codigo_lre else 0,
                                payslip.indicadores_id.mutualidad_id.codigo_lre if payslip.indicadores_id.mutualidad_id.codigo_lre else 0,
                                payslip.contract_id.carga_familiar,
                                payslip.contract_id.carga_familiar_maternal,
                                payslip.contract_id.carga_familiar_invalida,
                                payslip.contract_id.tramo_asig_fam,   
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                0,
                                int(self.get_dias_trabajados(payslip and payslip[0] or 0)),
                                int(30-self.get_dias_trabajados(payslip and payslip[0] or 0)) if self.get_dias_trabajados(payslip and payslip[0] or 0)<30 else 0,
                                #1117 Número días de vacaciones en el mes
                                0,
                                #1118 Subsidio trabajador joven
                                0,
                                #1154 Puesto trabajo pesado
                                0,
                                #1155 Ahorro previsional voluntario individual
                                0,
                                #1157 Ahorro previsional voluntario colectivo 
                                0,
                                #1131 Indemnización a todo evento (Art. 164) 
                                0,
                                #Tasa indemnización a todo evento (Art. 164)
                                4.11,
                                #2101 Sueldo 
                                int(self.get_payslip_lines_value_2(payslip,'SUELDO')) if self.get_payslip_lines_value_2(payslip,'SUELDO') else 0,
                                int(self.get_payslip_lines_value_2(payslip,'HEX50')) if self.get_payslip_lines_value_2(payslip,'HEX50') else 0,
                                int(self.get_payslip_lines_value_2(payslip,'COMI')) if self.get_payslip_lines_value_2(payslip,'COMI') else 0,
                                #2104 Semana corrida mensual (Art. 45)
                                0,
                                #2104 Semana corrida mensual (Art. 45)
                                0,
                                int(self.get_payslip_lines_value_2(payslip,'GRAT')) if self.get_payslip_lines_value_2(payslip,'GRAT') else 0,
                                #2107 Recargo 30% día domingo (Art. 38)
                                0,
                                #2108 Remuneración variable pagada en vacaciones (Art. 71)
                                0,
                                #2109 Remuneración variable pagada en clausura (Art. 38 DFL 2)
                                0,
                                int(self.get_payslip_lines_value_2(payslip,'AGUI')) if self.get_payslip_lines_value_2(payslip,'AGUI') else 0,
                                #2111 Bonos u otras remuneraciones fijas mensuales
                                0,
                                #2112 Tratos (mensual) 
                                0,
                                #2113 Bonos u otras remuneraciones variables mensuales o superiores a un mes
                                int(self.get_payslip_lines_value_nombre(payslip,'BONO')) if self.get_payslip_lines_value_nombre(payslip,'BONO') else 0,
                                #2114 Ejercicio opción no pactada en contrato (Art. 17 N°8 LIR) 
                                0,
                                #2115 Beneficios en especie constitutivos de remuneración 
                                0,
                                #2116 Remuneraciones bimestrales (devengo en dos meses)
                                0,
                                #2117 Remuneraciones trimestrales (devengo en tres meses) 
                                0,
                                #2118 Remuneraciones cuatrimestral (devengo en cuatro meses)
                                0,
                                #2119 Remuneraciones semestrales (devengo en seis meses)
                                0,
                                #2120 Remuneraciones anuales (devengo en doce meses) 
                                0,
                                #2121 Participación anual (devengo en doce meses) 
                                0,
                                #2122 Gratificación anual (devengo en doce meses) 
                                0,
                                #2123 Otras remuneraciones superiores a un mes
                                0,
                                #2124 Pago por horas de trabajo sindical
                                0,
                                #2161 Sueldo empresarial 
                                0,
                                #2201 Subsidio por incapacidad laboral por licencia médica - total mensual 
                                0,
                                #2202 Beca de estudio (Art. 17 N°18 LIR)
                                0,
                                #2203 Gratificaciones de zona (Art. 17 N°27) 
                                0,
                                #2204 Otros ingresos no constitutivos de renta (Art. 17 N°29 LIR)
                                0,
                                #2301 Colación total mensual (Art. 41)
                                int(self.get_payslip_lines_value_2(payslip,'COL')) if self.get_payslip_lines_value_2(payslip,'COL') else 0,
                                #2302 Movilización total mensual (Art. 41) 
                                int(self.get_payslip_lines_value_2(payslip,'MOV')) if self.get_payslip_lines_value_2(payslip,'MOV') else 0,
                                #2303 Viáticos total mensual (Art. 41) 
                                int(self.get_payslip_lines_value_2(payslip,'VIASAN')) if self.get_payslip_lines_value_2(payslip,'VIASAN') else 0,
                                #2304 Asignación de pérdida de caja total mensual (Art. 41) 
                                0,
                                #2305 Asignación de desgaste herramienta total mensual (Art. 41) 
                                0,
                                #2311 Asignación familiar legal total mensual (Art. 41) 
                                int(self.get_payslip_lines_value_2(payslip,'ASIGFAM')) if self.get_payslip_lines_value_2(payslip,'ASIGFAM') else 0,
                                #2306 Gastos por causa del trabajo (Art. 41) 
                                0,
                                #2307 Gastos por cambio de residencia (Art. 53) 
                                0,
                                #2308 Sala cuna (Art. 203) 
                                0,
                                #2309 Asignación trabajo a distancia o teletrabajo
                                0,
                                #2347 Depósito convenido hasta UF 900 
                                0,
                                #2310 Alojamiento por razones de trabajo (Art. 17 N°14 LIR) 
                                0,
                                #2312 Asignación de traslación (Art. 17 N°15 LIR)
                                0,
                                #2313 Indemnización por feriado legal 
                                0,
                                #2314 Indemnización años de servicio 
                                0,
                                #2315 Indemnización sustitutiva del aviso previo
                                0,
                                #2316 Indemnización fuero maternal (Art. 163 bis) 
                                0,
                                #2331 Indemnización a todo evento (Art. 164)
                                0,
                                #2417 Indemnizaciones voluntarias tributables
                                0,
                                #2418 Indemnizaciones contractuales tributables
                                0,
                                #3141 Cotización obligatoria previsional (AFP o IPS)
                                int(self.get_payslip_lines_value_2(payslip,'PREV')) if self.get_payslip_lines_value_2(payslip,'PREV') else 0,
                                #3143 Cotización obligatoria salud 7%
                                int(self.get_payslip_lines_value_2(payslip,'SALUD')) if self.get_payslip_lines_value_2(payslip,'SALUD') else 0,
                                #3144 Cotización voluntaria para salud 
                                int(self.get_payslip_lines_value_2(payslip,'ADISA')) if self.get_payslip_lines_value_2(payslip,'ADISA') else 0,
                                #3151 Cotización AFC - trabajador 
                                int(self.get_payslip_lines_value_2(payslip,'SECE')) if self.get_payslip_lines_value_2(payslip,'SECE') else 0,
                                #3146 Cotizaciones técnico extranjero para seguridad social fuera de Chile
                                0,
                                #3147 Descuento depósito convenido hasta UF 900 anual 
                                0,
                                #3155 Cotización ahorro previsional voluntario individual modalidad A 
                                int(self.get_payslip_lines_value_2(payslip,'APV')) if self.get_payslip_lines_value_2(payslip,'APV') else 0,
                                #3156 Cotización ahorro previsional voluntario individual modalidad B hasta UF 50 
                                0,
                                #3157 Cotización ahorro previsional voluntario colectivo modalidad A
                                0,
                                #3158 Cotización ahorro previsional voluntario colectivo modalidad B hasta UF 50 
                                0,
                                #3161 Impuesto retenido por remuneraciones 
                                int(self.get_payslip_lines_value_2(payslip,'IMPUNI')) if self.get_payslip_lines_value_2(payslip,'IMPUNI') else 0,
                                #3162 Impuesto retenido por indemnizaciones
                                0,
                                #3163 Mayor retención de impuestos solicitada por el trabajador
                                0,
                                #3164 Impuesto retenido por reliquidación remuneraciones devengadas en otros períodos
                                0,
                                #3165 Diferencia de impuesto por reliquidación remuneraciones devengadas en este período
                                0,
                                #3166 Retención préstamo clase media 2020 (Ley 21.252)
                                int(self.get_payslip_lines_value_2(payslip,'PTMOSOLID')) if self.get_payslip_lines_value_2(payslip,'PTMOSOLID') else 0,
                                #3167 Rebaja zona extrema DL 889 
                                0,
                                #3171 Cuota sindical 1 Int 8 OPCIONAL 
                                0,
                                #3172 Cuota sindical 2 Int 8 OPCIONAL 
                                0,
                                #3173 Cuota sindical 3 Int 8 OPCIONAL 
                                0,
                                #3174 Cuota sindical 4 Int 8 OPCIONAL 
                                0,
                                #3175 Cuota sindical 5 Int 8 OPCIONAL 
                                0,
                                #3176 Cuota sindical 6 Int 8 OPCIONAL 
                                0,
                                #3177 Cuota sindical 7 Int 8 OPCIONAL 
                                0,
                                #3178 Cuota sindical 8 Int 8 OPCIONAL 
                                0,
                                #3179 Cuota sindical 9 Int 8 OPCIONAL 
                                0,
                                #3180 Cuota sindical 10 Int 8 OPCIONAL
                                0,
                                #3110 Crédito social CCAF
                                int(self.get_payslip_lines_value_2(payslip,'PCCAF')) if self.get_payslip_lines_value_2(payslip,'PCCAF') else 0,
                                #3181 Cuota vivienda o educación (Art. 58) 
                                0,
                                #3182 Crédito cooperativas de ahorro (Art 54. Ley Coop.) 
                                0,
                                #3183 Otros descuentos autorizados y solicitados por el trabajador
                                0,
                                #3154 Cotización adicional trabajo pesado - trabajador 
                                0,
                                #3184 Donaciones culturales y de reconstrucción
                                0,
                                #3185 Otros descuentos (Art. 58)
                                0,
                                #3186 Pensiones de alimentos 
                                0,
                                #3187 Descuento mujer casada (Art. 59) 
                                0,
                                #3188 Descuentos por anticipos y préstamos 
                                int(self.get_payslip_lines_value_2(payslip,'ASUE')) if self.get_payslip_lines_value_2(payslip,'ASUE') else 0,
                                #4151 Aporte AFC - empleador 
                                int(self.get_payslip_lines_value_2(payslip,'SECEEMP')) if self.get_payslip_lines_value_2(payslip,'SECEEMP') else 0,
                                #4152 Aporte empleador seguro accidentes del trabajo y Ley SANNA (Ley 16.744)
                                int(self.get_payslip_lines_value_2(payslip,'MUT')) if self.get_payslip_lines_value_2(payslip,'MUT') else 0,
                                #4131 Aporte empleador indemnización a todo evento (Art. 164) 
                                0,
                                #4154 Aporte adicional trabajo pesado - empleador 
                                0,
                                #4155 Aporte empleador seguro invalidez y sobrevivencia 
                                int(self.get_payslip_lines_value_2(payslip,'SIS')) if self.get_payslip_lines_value_2(payslip,'SIS') else 0,
                                #4157 Aporte empleador ahorro previsional voluntario colectivo 
                                0,
                                #5201 Total haberes 
                                int(self.get_payslip_lines_value_2(payslip,'HAB')) if self.get_payslip_lines_value_2(payslip,'HAB') else 0,
                                #5210 Total haberes imponibles y tributables                       
                                int(self.get_payslip_lines_value_2(payslip,'TRIBU')) if self.get_payslip_lines_value_2(payslip,'TRIBU') else 0,
                                #5220 Total haberes imponibles no tributables 
                                0,
                                #5230 Total haberes no imponibles y no tributables 
                                int(self.get_payslip_lines_value_2(payslip,'TOTNOI')) if self.get_payslip_lines_value_2(payslip,'TOTNOI') else 0,
                                #5240 Total haberes no imponibles y tributables 
                                0,
                                #5301 Total descuentos 
                                int(self.get_payslip_lines_value_2(payslip,'TDE')) if self.get_payslip_lines_value_2(payslip,'TDE') else 0,
                                #5361 Total descuentos impuestos a las remuneraciones 
                                int(self.get_payslip_lines_value_2(payslip,'IMPUNI')) if self.get_payslip_lines_value_2(payslip,'IMPUNI') else 0,
                                #5362 Total descuentos impuestos por indemnizaciones
                                0,
                                #5341 Total descuentos por cotizaciones del trabajador
                                int(self.get_payslip_lines_value_2(payslip,'TODELE')) if self.get_payslip_lines_value_2(payslip,'TODELE') else 0,
                                #5302 Total otros descuentos
                                int(self.get_payslip_lines_value_2(payslip,'TOD')) if self.get_payslip_lines_value_2(payslip,'TOD') else 0,
                                #5410 Total aportes empleador
                                int(self.get_payslip_lines_value_2(payslip,'APORTE')) if self.get_payslip_lines_value_2(payslip,'APORTE') else 0,
                                #5501 Total líquido 
                                int(self.get_payslip_lines_value_2(payslip,'LIQ')) if self.get_payslip_lines_value_2(payslip,'LIQ') else 0,
                                #5502 Total indemnizaciones
                                0,
                                #5564 Total indemnizaciones tributables
                                0,
                                #5565 total indemnizaciones no tributables 
                                0,
                             ]
            writer.writerow([str(l) for l in line_employee])
        self.write({'file_data': base64.encodebytes(output.getvalue().encode()),
                    'file_name': "Lre_%s.csv" % (self.date_to),
                    })
        self.clear_caches()
        return self.show_view(u'LRE Generado')
