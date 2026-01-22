from django.contrib import admin
from .models import CustomUser, Appointment, DaySchedule

# Esto personaliza cómo se ve el usuario en el panel
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'role', 'first_name', 'last_name', 'is_staff')
    list_filter = ('role', 'is_staff')
    search_fields = ('phone_number', 'first_name')
    ordering = ('phone_number',)

# Esto personaliza las citas
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'client', 'status') # Columnas visibles
    list_filter = ('status', 'date') # Filtros laterales
    search_fields = ('client__phone_number',) # Buscador por teléfono del cliente
    ordering = ('date', 'time')

# Esto personaliza los días de trabajo
class DayScheduleAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_working_day', 'start_time', 'end_time', 'note')
    list_filter = ('is_working_day',)
    ordering = ('date',)

# Registramos los modelos
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(DaySchedule, DayScheduleAdmin)