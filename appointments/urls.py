from django.urls import path
from . import views

urlpatterns = [
    # --- RUTA PRINCIPAL (AHORA ES LA LANDING) ---
    path('', views.landing_page, name='home'),

    # --- RUTA DEL CALENDARIO (AHORA EN /RESERVAR) ---
    path('reservar/', views.booking_calendar, name='booking_calendar'),
    
    # Ruta para obtener las horas (AJAX)
    path('get-hours/', views.get_available_hours, name='get_hours'),
    
    # Ruta para confirmar la cita
    path('book/<str:date_str>/<str:time_str>/', views.book_appointment, name='book_appointment'),
    
    # Ruta de éxito
    path('success/', views.booking_success, name='booking_success'),

    # --- RUTAS PARA MIS CITAS (CLIENTE) ---
    path('mis-citas/', views.my_appointments, name='my_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('postpone/<int:appointment_id>/', views.postpone_appointment, name='postpone_appointment'),
    
    # --- RUTAS DEL BARBERO (ADMINISTRACIÓN) ---
    path('admin-barber/', views.barber_login, name='barber_login'),
    path('dashboard/', views.barber_dashboard, name='barber_dashboard'),
    path('logout/', views.barber_logout, name='barber_logout'),
    
    # --- GESTIÓN DE HORARIOS ---
    path('admin-barber/settings/', views.barber_settings, name='barber_settings'),
    path('admin-barber/update-schedule/<int:schedule_id>/', views.update_schedule, name='update_schedule'),
    
    # Acciones de los botones (Dashboard)
    path('mark-completed/<int:appointment_id>/', views.mark_completed, name='mark_completed'),
    path('mark-noshow/<int:appointment_id>/', views.mark_noshow, name='mark_noshow'),
]