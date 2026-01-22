from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField 

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('El número de teléfono es obligatorio')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None 
    # Usamos PhoneNumberField como tenías configurado
    phone_number = PhoneNumberField(unique=True, region='SV', verbose_name="Teléfono")
    
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="Apodo")

    # --- NUEVO CAMPO DE SEGURIDAD ---
    # Guardará el PIN de 4 dígitos para validar identidad
    security_pin = models.CharField(max_length=4, blank=True, null=True, verbose_name="PIN de Seguridad")

    ROLE_CHOICES = [
        ('CLIENT', 'Cliente'),
        ('BARBER', 'Peluquero'),
        ('ADMIN', 'Administrador'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = [] 

    objects = CustomUserManager()

    def __str__(self):
        display_name = self.nickname if self.nickname else self.first_name
        return f"{self.phone_number} - {display_name}"

class DaySchedule(models.Model):
    date = models.DateField(unique=True, verbose_name="Fecha")
    is_working_day = models.BooleanField(default=True, verbose_name="¿Se trabaja?")
    
    # CAMBIO: Actualizamos a 08:00 y 18:00 para coincidir con la nueva lógica
    start_time = models.TimeField(default="08:00", verbose_name="Hora Inicio")
    end_time = models.TimeField(default="18:00", verbose_name="Hora Fin")
    
    is_lunch_break_active = models.BooleanField(default=False, verbose_name="¿Tomar Almuerzo?")
    lunch_start_time = models.TimeField(default="13:00", verbose_name="Hora Inicio Almuerzo")
    
    note = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        estado = "Abierto" if self.is_working_day else "Cerrado"
        return f"{self.date} - {estado}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('CONFIRMED', 'Confirmada'),
        ('CANCELLED', 'Cancelada'),   
        ('RESCHEDULED', 'Postergada/Reagendada'), 
        ('COMPLETED', 'Completada'),
        ('NOSHOW', 'No Asistió'), # CAMBIO: Agregado oficialmente
    ]

    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField(verbose_name="Fecha de la Cita")
    time = models.TimeField(verbose_name="Hora de la Cita")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # CAMBIO CRÍTICO: Eliminamos unique_together para permitir marcar 'No Vino' sin errores
        # unique_together = ('date', 'time', 'status') 
        ordering = ['date', 'time'] # Opcional: Para que salgan ordenadas

    def __str__(self):
        return f"{self.date} {self.time} - {self.client.phone_number}"