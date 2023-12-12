# -*- coding: utf-8 -*-

from odoo import models, fields, api  #Importando librerias
from odoo.exceptions import ValidationError #Importando excepciones de odoo
from odoo import _
import datetime
import logging
import re

_logger = logging.getLogger(__name__) #Información que obtinene del fichero de configuración

#Ejemplo de herencia
class developer(models.Model):
   _name = 'res.partner' #Asignando Nombre del modelo que heredare
   _inherit = 'res.partner' #Indicamos la herencia y el modulo a heredar y todos los campos que añada en esta clase se añadiran en el modelo res.partner(contactos)

   is_dev = fields.Boolean()
   access_code = fields.Char()

   technologies = fields.Many2many('manage.technology',
                                   relation='developer_technologies',
                                   column1='developer_id',
                                   column2='technologies_id')
   
   tasks = fields.Many2many('manage.task',
                                   relation='developer_task',
                                   column1='developer_id',
                                   column2='task_id')
   
   bugs = fields.Many2many('manage.bug',
                                   relation='developer_bugs',
                                   column1='developer_id',
                                   column2='bug_id')
   
   improvements = fields.Many2many('manage.improvement',
                                   relation='developer_improvements',
                                   column1='developer_id',
                                   column2='improvement_id')
   
   #Comprobar el contenido de ese campo
   @api.constrains('access_code')
   def _check_code(self):
      for dev in self:
         regex = re.compile('^[0-9]{8}[a-z]', re.I) #La cadena que reciba accesCode tiene que cumplir este patron (tema expresiones regulares en python)
         if regex.match(dev.access_code):
            _logger.info('Código de acceso generado correctamente')
         else:
            raise ValidationError('Formato de código de acceso incorrecto')
   
   _sql_constraints = [('access_code_unique', 'unique(access_code)', 'Access code ya existente.')]


   @api.onchange('is_dev')
   def _onchange_is_dev(self):
      categories = self.env['res.partner.category'].search([('name', '=','Devs')])
      if len(categories) > 0:
         category = categories[0]
      else:
         category = self.env['res.partner.category'].create({'name':'Devs'})
      self.category_id = [(4, category.id)]



#Creando el modelo proyecto
class project(models.Model):
   _name = 'manage.project' #Asignando Nombre al modelo
   _description = 'manage.project' #Aseignando una pequeña descripción al modelo

   name = fields.Char()
   descriptiones = fields.Text()
   histories = fields.One2many(comodel_name="manage.history", inverse_name="project")
   is_developement = fields.Boolean()
   is_read = fields.Boolean()
   is_tree = fields.Boolean()
   is_test1 = fields.Text()
   is_test2 = fields.Text()
   is_test3 = fields.Text()
   is_test4 = fields.Text()
   is_test5 = fields.Text()
   is_test6 = fields.Text()

#Creando modelo historias de usuario
class history(models.Model):
   _name = 'manage.history' #Asignando Nombre al modelo
   _description = 'manage.history' #Asignando una pequeña descripción al modelo

   name = fields.Char()
   description = fields.Text()
   project = fields.Many2one("manage.project", ondelete="set null")
   #campo relacionado con el modelo task
   tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name="history")
   #Campo relacionado con el modelo tecnology
   used_technologies = fields.Many2many("manage.technology", compute="_get_used_technologies")

   def _get_used_technologies(self):
      for history in self:
         technologies = None
         for task in history.tasks:
            if not technologies:
               technologies = task.technologies
            else:
               technologies = technologies + task.technologies
         history.used_technologies = technologies

#Creando un modelo task
class task(models.Model): #creando la clase, todos los modolos se herendan de models.Models
   ##Campos propios de los modelos
   _name = 'manage.task' #Asignando Nombre al modelo
   _description = 'manage.task' #Aseignando una pequeña descripción al modelo

   #2da forma de declarar un campo computado con valor por defecto - directamente con lambda en este caso para declarar la fecha actual como valor por defecto 
   definition_date = fields.Datetime(default=lambda p: datetime.datetime.now())
   #Campo computado que no se almacena en bd, Campo relacional que coje el campo de otro modelo
   project = fields.Many2one('manage.project', related = 'history.project', readonly=True) #Relación 'history.project', porque en el modelo history se relaciona con project
   ##Campo computado
   code = fields.Char(compute="_get_code") #Campo que se calcula cada vez que se hace un cambio (no se almacena en la base de datos)
   ##Campo que creamos , es decir que aparecera en el modulo, si no agregamos nada en los parentesis por defecto tomara el nombre de la variable en este caso name
   name = fields.Char(string="Nombres", readonly=False, required=True, help='Introduzca el nombre') #cambiando el label por nombres, solo lectura en falso, el campo sea obligatorio, y un mensaje de ayuda
   #campo relacionado con el modelo history
   history = fields.Many2one("manage.history", ondelete="set null", help="Historia relacionada")
   description = fields.Text() # Campo de tipo Text() -> nos permite poner texto mas amplio
   #creation_date = fields.Date() # campo tipo fecha,, campo no necesario porque por defecto el modelo crea un campo fecha de creación
   start_date = fields.Datetime() # campo tipo fecha y hora
   end_date = fields.Datetime() # campo tipo fecha y hora
   is_paused = fields.Boolean() # campo tipo booleano, verdadero o falso
   # Campo relacionado, sobre el modelo "manage.sprint", relacion de muchos a uno, muchas tareas perteneceran a un sprint
   sprint = fields.Many2one("manage.sprint", compute="_get_sprint", store=True) #colocando atributos
   technologies = fields.Many2many(comodel_name="manage.technology", relation="technologies_tasks", column1="task_id", column2="technology_id") #atributos, nombre del modelo relacionado, el nombre de la tabla que crea, nombre de los campos relacionados


   #Creando funcion que calcula el campo code asignandole un codigo si es que no tiene springs y si tiene cambia el codigo por el nombre y numero del sprint
   #@api.one
   def _get_code(self):
      for task in self:
         try:
               task.code = "TSK_"+str(task.id)
               _logger.debug("Código generado: "+task.code) #Mostrar distintos tipos de informacion en el log en este caso debug 
         except:
            raise ValidationError(_("Generación de código errónea")) #Excepcion que aparece como mensaje dentro de odoo y tambien en el log

   @api.depends('code')
   def _get_sprint(self):
      for task in self:
         #sprints = self.env['manage.sprint'].search([('project.id', '=',task.history.project.id)])
         if isinstance(task.history.project.id, models.NewId):
            id_project = int(task.history.project.id.origin)
         else:
            id_project = task.history.project.id
         sprints = self.env['manage.sprint'].search([('project.id', '=', id_project)])
         found = False
         for sprint in sprints:
            if isinstance(sprint.end_date, datetime.datetime) and sprint.end_date > datetime.datetime.now():
               task.sprint = sprint.id
               found = True
         if not found:
            task.sprint = False

#Función para el campo computado con valor por defecto
#   def _get_definition_date(self):
#      return datetime.datetime.now()

   def _getDefaultDev(self):
      dev = self.browse(self._context.get('current_developer'))
      if dev:
         return [dev.id]
      else:
         return []

   developers = fields.Many2many(comodel_name='res.partner',
                                 relation='developers_tasks',
                                 column1='task_id',
                                 column2='developer_id',
                                 default=_getDefaultDev)

class bug(models.Model): #creando la clase bug

   _name = 'manage.bug' #Asignando Nombre al modelo
   _description = 'manage.bug' #Asignando una pequeña descripción al modelo
   _inherit = 'manage.task' # Heredando los atributos de manage task a este nuevo modelo

   technologies = fields.Many2many(comodel_name='manage.technology',
                                   relation='technologies_bugs',
                                   column1='bug_id',
                                   column2='technologies_id')
   
   tasksLinked = fields.Many2many(comodel_name='manage.task',
                                   relation='tasks_bugs',
                                   column1='bug_id',
                                   column2='task_id')
   
   bugsLinked = fields.Many2many(comodel_name='manage.bug',
                                   relation='bugs_bugs',
                                   column1='bug1_id',
                                   column2='bug2_id')
   
   improvementsLinked = fields.Many2many(comodel_name='manage.improvement',
                                   relation='improvements_bugs',
                                   column1='bug_id',
                                   column2='improvement_id')
   
   developers = fields.Many2many(comodel_name='res.partner',
                                   relation='developers_bugs',
                                   column1='bug_id',
                                   column2='developer_id')
   

class improvement(models.Model): #creando la clase improvement

   _name = 'manage.improvement' #Asignando Nombre al modelo
   _description = 'manage.improvement' #Asignando una pequeña descripción al modelo
   _inherit = 'manage.task' # Heredando los atributos de manage task a este nuevo modelo

   technologies = fields.Many2many(comodel_name='manage.technology',
                                   relation='technologies_improvements',
                                   column1='improvement_id',
                                   column2='technologies_id')
   
   historiesLinked = fields.Many2many('manage.history')
   
   developers = fields.Many2many(comodel_name='res.partner',
                                   relation='developers_improvement',
                                   column1='improvement_id',
                                   column2='developer_id')

#Añadiendo un nuevo modelo sprint, para relacionar campos, en este caso tomaremos la metodologia scrum donde se hacen sprints cada cierto tiempo
class sprint(models.Model):
   _name = 'manage.sprint'
   _description = 'manage.sprint'

   #Campo relacionado con el modelo project
   project = fields.Many2one("manage.project")
   name = fields.Char()
   description = fields.Text()
   duration = fields.Integer(default=15) #Campo por defecto
   start_date = fields.Datetime()
   end_date = fields.Datetime(compute="_get_end_date", store=True) #Campo calculado, se pone automaticamente la fecha fin segun la duracion y el inicio de  fecha (se guarda en base de datos)
   #las relaciones one2many es una consulta a partir de la tabla que se crea en la relacion many2one,
   #en este caso para establecer una relacion one2many necesitamos la tabla many2one de sprint
   tasks = fields.One2many(string="Tareas", comodel_name="manage.task", inverse_name='sprint') #Colocando atributos, etiqueta, nombre de modelo relacionado, nombre de campo relacionado

   #Creando funcion para calcular campo de duracion del sprint, 
   # cuando ponemos el numero de duracion en el campo duración y le ponemos la fecha de inicio, automaticamente se calculara la fecha de fin
   @api.depends('start_date', 'duration') # end_date solo se recalculara solo cuando modifiquen estos 2 campos
   def _get_end_date(self): #importante poner self para que pueda acceder a todo lo que hay en el modulo
      for sprint in self:
         if isinstance(sprint.start_date, datetime.datetime) and sprint.duration > 0:
            sprint.end_date = sprint.start_date + datetime.timedelta(days=sprint.duration)
         else:
            sprint.end_date = sprint.start_date


#Añadiendo un nuevo modelo tecnology
class technology(models.Model):
   _name = 'manage.technology'
   _description = 'manage.technology'

   name = fields.Char()
   description = fields.Text()

   photo = fields.Image(max_width=200, max_height=200) #Campo de tipo Image que hereda del tipo binario, el tipo image permite redimensionar las imagenes
   tasks = fields.Many2many(comodel_name="manage.task",
                            relation="technologies_tasks",
                            column1="technology_id",
                            column2="task_id")#atributos, nombre del modelo relacionado, el nombre de la tabla que crea, nombre de los campos relacionados
   