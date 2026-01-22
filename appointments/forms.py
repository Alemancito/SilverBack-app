from django import forms
from phonenumber_field.formfields import PhoneNumberField
from .models import DaySchedule # <--- IMPORTANTE: Agregamos esto para el nuevo formulario

class ClientBookingForm(forms.Form):
    phone_number = PhoneNumberField(
        region='SV',
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={
            'id': 'phone_field',
            'class': 'form-control form-control-lg',
            'autocomplete': 'off' # Intento 1 de bloqueo
        })
    )
    
    first_name = forms.CharField(
        max_length=30, 
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': 'Ej: Carlos',
            'autocomplete': 'off'
        })
    )
    
    last_name = forms.CharField(
        max_length=30, 
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': 'Ej: López',
            'autocomplete': 'off'
        })
    )
    
    nickname = forms.CharField(
        max_length=30, 
        required=False,
        label="Apodo (Opcional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': 'Ej: Charly / El Flaco',
            'autocomplete': 'off'
        })
    )

    # --- CAMPO PIN ---
    pin = forms.CharField(
        max_length=4, 
        min_length=4,
        label="PIN de Seguridad (4 dígitos)",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg text-center fw-bold', 
            'placeholder': '••••',
            'inputmode': 'numeric', 
            'pattern': '[0-9]*',    
            'autocomplete': 'new-password', # Truco para evitar auto-fill
            'data-lpignore': 'true' # Truco para LastPass
        })
    )

# --- NUEVO: FORMULARIO PARA GESTIÓN DE HORARIOS ---
class BarberScheduleForm(forms.ModelForm):
    class Meta:
        model = DaySchedule
        fields = ['is_working_day', 'start_time', 'end_time', 'is_lunch_break_active', 'lunch_start_time', 'note']